import asyncio
import json
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Conversation, LlmCall, Message, RetrievalEvent
from app.schemas.api import ChatRequest
from app.services.demo import build_demo_answer
from app.services.domain_profiles import (
    get_allowed_access_levels,
    get_domain_profile,
)
from app.services.embedding import EmbeddingNotConfigured, get_embedding_client
from app.services.llm import LlmNotConfigured, OpenAICompatibleChatClient
from app.services.safety import crisis_support_message, detect_safety_issue
from app.vectorstores import SearchFilters, get_vector_store

router = APIRouter()


@router.post("/stream")
async def stream_chat(payload: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _generate_events(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _generate_events(payload: ChatRequest) -> AsyncIterator[str]:
    request_id = uuid.uuid4()
    started = time.perf_counter()
    conversation_id = payload.conversation_id

    yield _sse(
        "meta",
        {
            "request_id": str(request_id),
            "conversation_id": str(conversation_id) if conversation_id else None,
            "mode": payload.mode,
        },
    )

    safety = detect_safety_issue(payload.question)
    if safety.level == "crisis":
        yield _sse(
            "safety",
            {
                "level": safety.level,
                "action": safety.action,
                "request_id": str(request_id),
            },
        )
        answer = crisis_support_message()
        async for event in _stream_fixed_answer(answer):
            yield event
        yield _sse(
            "done",
            {
                "message_id": None,
                "finish_reason": "crisis_support",
                "total_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        return

    if not settings.demo_mode and not settings.embedding_api_key:
        yield _sse(
            "error",
            {
                "code": "EMBEDDING_NOT_CONFIGURED",
                "message": "EMBEDDING_API_KEY is required before chat can run.",
                "request_id": str(request_id),
                "retryable": False,
            },
        )
        return
    if not settings.demo_mode and not settings.llm_api_key:
        yield _sse(
            "error",
            {
                "code": "LLM_NOT_CONFIGURED",
                "message": "LLM_API_KEY is required before chat can run.",
                "request_id": str(request_id),
                "retryable": False,
            },
        )
        return

    profile = get_domain_profile(payload.mode)

    async with SessionLocal() as db:
        conversation = await _get_or_create_conversation(
            db,
            conversation_id,
            payload.knowledge_base_id,
            payload.question,
            payload.mode,
        )
        conversation_id = conversation.id
        yield _sse(
            "meta",
            {
                "request_id": str(request_id),
                "conversation_id": str(conversation_id),
                "mode": payload.mode,
            },
        )

        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=payload.question,
            status="completed",
            safety_level=safety.level,
            request_id=request_id,
        )
        db.add(user_message)
        await db.commit()

        embedding_started = time.perf_counter()
        try:
            embedding_result = await get_embedding_client().embed([payload.question])
        except EmbeddingNotConfigured:
            yield _sse(
                "error",
                {
                    "code": "EMBEDDING_NOT_CONFIGURED",
                    "message": "Embedding client is not configured.",
                    "request_id": str(request_id),
                    "retryable": False,
                },
            )
            return
        embedding_ms = int((time.perf_counter() - embedding_started) * 1000)

        search_started = time.perf_counter()
        requested_doc_type = payload.filters.doc_type
        if requested_doc_type and requested_doc_type not in profile.default_doc_types:
            yield _sse(
                "error",
                {
                    "code": "INVALID_MODE_FILTER",
                    "message": (
                        f"Document type '{requested_doc_type}' is not available "
                        f"in {payload.mode} mode."
                    ),
                    "request_id": str(request_id),
                    "retryable": False,
                },
            )
            return

        search_filters = SearchFilters(
            domain=profile.domain,
            doc_types=(
                (requested_doc_type,)
                if requested_doc_type
                else profile.default_doc_types
            ),
            allowed_access_levels=get_allowed_access_levels(),
            audience=payload.filters.audience,
            assessment_code=payload.filters.assessment_code,
            assessment_version=payload.filters.assessment_version,
        )
        try:
            results = await get_vector_store(db).search(
                query_vector=embedding_result.vectors[0],
                top_k=settings.retrieval_top_k,
                knowledge_base_id=payload.knowledge_base_id,
                filters=search_filters,
            )
        except NotImplementedError as exc:
            yield _sse(
                "error",
                {
                    "code": "VECTOR_STORE_NOT_IMPLEMENTED",
                    "message": str(exc),
                    "request_id": str(request_id),
                    "retryable": False,
                },
            )
            return
        search_ms = int((time.perf_counter() - search_started) * 1000)
        minimum_similarity = 0.05 if settings.demo_mode else settings.retrieval_min_similarity
        results = [result for result in results if result.score >= minimum_similarity]
        sources = [
            {
                "id": f"S{index}",
                "chunk_id": str(result.chunk_id),
                "document_id": str(result.document_id),
                "name": result.file_name,
                "page": result.page_no,
                "section": " / ".join(result.section_path) if result.section_path else None,
                "score": round(result.score, 4),
                "excerpt": result.content[:300],
                "doc_type": result.doc_type,
                "audience": result.audience,
                "assessment_code": result.assessment_code,
                "assessment_version": result.assessment_version,
                "review_status": result.review_status,
            }
            for index, result in enumerate(results, start=1)
        ]
        prompt_sources = [
            {
                "id": f"S{index}",
                "name": result.file_name,
                "page": result.page_no,
                "section": " / ".join(result.section_path) if result.section_path else None,
                "assessment_code": result.assessment_code,
                "assessment_version": result.assessment_version,
                "content": result.content,
            }
            for index, result in enumerate(results, start=1)
        ]
        yield _sse("sources", {"sources": sources})

        if not results:
            answer = "当前文档中没有找到足够依据回答这个问题。"
            async for event in _stream_fixed_answer(answer):
                yield event
            yield _sse(
                "done",
                {
                    "message_id": None,
                    "finish_reason": "insufficient_context",
                    "total_ms": int((time.perf_counter() - started) * 1000),
                    "mode": payload.mode,
                },
            )
            return

        user_prompt = _build_prompt(payload.question, prompt_sources)
        assistant_parts: list[str] = []
        first_token_ms: int | None = None

        if settings.demo_mode:
            answer = build_demo_answer(payload.question, results, payload.mode)
            first_token_ms = int((time.perf_counter() - started) * 1000)
            assistant_parts.append(answer)
            for offset in range(0, len(answer), 24):
                yield _sse("token", {"delta": answer[offset : offset + 24]})
                await asyncio.sleep(0)
        else:
            try:
                async for token in OpenAICompatibleChatClient().stream(
                    profile.system_prompt,
                    user_prompt,
                ):
                    if first_token_ms is None:
                        first_token_ms = int((time.perf_counter() - started) * 1000)
                    assistant_parts.append(token)
                    yield _sse("token", {"delta": token})
            except LlmNotConfigured:
                yield _sse(
                    "error",
                    {
                        "code": "LLM_NOT_CONFIGURED",
                        "message": "LLM client is not configured.",
                        "request_id": str(request_id),
                        "retryable": False,
                    },
                )
                return

        answer = "".join(assistant_parts)
        llm_latency_ms = int((time.perf_counter() - started) * 1000)
        input_tokens = _estimate_tokens(profile.system_prompt) + _estimate_tokens(user_prompt)
        output_tokens = _estimate_tokens(answer)

        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            status="completed",
            request_id=request_id,
        )
        db.add(assistant_message)
        await db.flush()
        db.add(
            RetrievalEvent(
                request_id=request_id,
                message_id=assistant_message.id,
                query=payload.question,
                top_k=settings.retrieval_top_k,
                mode=payload.mode,
                filters_json=payload.filters.model_dump(exclude_none=True),
                source_versions=[
                    {
                        "document_id": str(result.document_id),
                        "assessment_code": result.assessment_code,
                        "assessment_version": result.assessment_version,
                        "review_status": result.review_status,
                    }
                    for result in results
                ],
                chunk_ids=[str(result.chunk_id) for result in results],
                scores=[result.score for result in results],
                embedding_ms=embedding_ms,
                search_ms=search_ms,
            )
        )
        db.add(
            LlmCall(
                request_id=request_id,
                provider="demo" if settings.demo_mode else "openai-compatible",
                model="demo-extractive" if settings.demo_mode else settings.llm_model,
                operation="chat",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=0,
                is_estimated=True,
                price_version="unconfigured",
                latency_ms=llm_latency_ms,
                first_token_ms=first_token_ms,
                success=True,
                metadata_json={"mode": payload.mode},
            )
        )
        await db.commit()

        yield _sse(
            "usage",
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "embedding_tokens": embedding_result.input_tokens,
                "cost": 0,
                "currency": "USD",
                "is_estimated": True,
            },
        )
        yield _sse(
            "done",
            {
                "message_id": str(assistant_message.id),
                "finish_reason": "stop",
                "total_ms": int((time.perf_counter() - started) * 1000),
                "mode": payload.mode,
            },
        )


async def _get_or_create_conversation(
    db,
    conversation_id,
    knowledge_base_id: str,
    title: str,
    mode: str,
) -> Conversation:
    if conversation_id is not None:
        conversation = await db.scalar(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        if conversation is not None:
            return conversation

    conversation = Conversation(
        id=conversation_id,
        knowledge_base_id=knowledge_base_id,
        mode=mode,
        title=title[:255],
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


def _build_prompt(question: str, sources: list[dict]) -> str:
    source_text = "\n\n".join(
        (
            f"[{source['id']}]\n"
            f"Source: {source['name']}, page: {source['page'] or 'n/a'}, "
            f"section: {source['section'] or 'n/a'}, "
            f"assessment: {source['assessment_code'] or 'n/a'}, "
            f"version: {source['assessment_version'] or 'n/a'}\n"
            f"Content: {source['content']}"
        )
        for source in sources
    )
    return f"Question:\n{question}\n\nSources:\n{source_text}"


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)


async def _stream_fixed_answer(answer: str) -> AsyncIterator[str]:
    yield _sse("token", {"delta": answer})


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
