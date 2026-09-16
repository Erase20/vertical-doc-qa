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
from app.services.embedding import EmbeddingNotConfigured, OpenAICompatibleEmbeddingClient
from app.services.llm import LlmNotConfigured, OpenAICompatibleChatClient
from app.vectorstores import get_vector_store

router = APIRouter()

SYSTEM_PROMPT = """You are a strict vertical-domain document QA assistant.
Use only the supplied source excerpts. If the excerpts do not contain enough
evidence, say so explicitly. Cite supporting facts as [S1], [S2], and so on.
Never invent a citation number that is not present in the supplied sources."""


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
        },
    )

    if not settings.embedding_api_key:
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
    if not settings.llm_api_key:
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

    async with SessionLocal() as db:
        conversation = await _get_or_create_conversation(
            db,
            conversation_id,
            payload.knowledge_base_id,
            payload.question,
        )
        conversation_id = conversation.id
        yield _sse(
            "meta",
            {"request_id": str(request_id), "conversation_id": str(conversation_id)},
        )

        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=payload.question,
            status="completed",
            request_id=request_id,
        )
        db.add(user_message)
        await db.commit()

        embedding_started = time.perf_counter()
        try:
            embedding_result = await OpenAICompatibleEmbeddingClient().embed([payload.question])
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
        try:
            results = await get_vector_store(db).search(
                query_vector=embedding_result.vectors[0],
                top_k=settings.retrieval_top_k,
                knowledge_base_id=payload.knowledge_base_id,
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
        results = [
            result
            for result in results
            if result.score >= settings.retrieval_min_similarity
        ]
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
            }
            for index, result in enumerate(results, start=1)
        ]
        prompt_sources = [
            {
                "id": f"S{index}",
                "name": result.file_name,
                "page": result.page_no,
                "section": " / ".join(result.section_path) if result.section_path else None,
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
                },
            )
            return

        user_prompt = _build_prompt(payload.question, prompt_sources)
        assistant_parts: list[str] = []
        first_token_ms: int | None = None

        try:
            async for token in OpenAICompatibleChatClient().stream(SYSTEM_PROMPT, user_prompt):
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
        input_tokens = _estimate_tokens(SYSTEM_PROMPT) + _estimate_tokens(user_prompt)
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
                chunk_ids=[str(result.chunk_id) for result in results],
                scores=[result.score for result in results],
                embedding_ms=embedding_ms,
                search_ms=search_ms,
            )
        )
        db.add(
            LlmCall(
                request_id=request_id,
                provider="openai-compatible",
                model=settings.llm_model,
                operation="chat",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=0,
                is_estimated=True,
                price_version="unconfigured",
                latency_ms=llm_latency_ms,
                first_token_ms=first_token_ms,
                success=True,
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
            },
        )


async def _get_or_create_conversation(
    db,
    conversation_id,
    knowledge_base_id: str,
    title: str,
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
            f"section: {source['section'] or 'n/a'}\n"
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
