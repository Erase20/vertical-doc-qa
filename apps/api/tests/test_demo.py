from uuid import uuid4

from app.services.demo import build_demo_answer, embed_text
from app.vectorstores.base import SearchResult


def test_demo_embedding_prefers_related_text() -> None:
    query = embed_text("项目使用 PostgreSQL 存储文档向量", 256)
    related = embed_text("PostgreSQL 用于存储文档和向量数据", 256)
    unrelated = embed_text("今天天气晴朗，适合外出散步", 256)

    related_score = sum(left * right for left, right in zip(query, related, strict=True))
    unrelated_score = sum(left * right for left, right in zip(query, unrelated, strict=True))

    assert related_score > unrelated_score


def test_demo_answer_includes_source_citation() -> None:
    document_id = uuid4()
    sources = [
        SearchResult(
            chunk_id=uuid4(),
            document_id=document_id,
            content="系统使用 PostgreSQL 和 pgvector 存储与检索文档向量。",
            score=0.8,
            file_name="architecture.md",
            page_no=None,
            section_path=["系统架构"],
            doc_type="guide",
            audience="public",
            assessment_code=None,
            assessment_version=None,
            review_status="approved",
        )
    ]

    answer = build_demo_answer("系统使用什么存储向量？", sources)

    assert "PostgreSQL" in answer
    assert "[S1]" in answer


def test_demo_answer_does_not_echo_question() -> None:
    question = "系统支持哪些文档格式？"
    sources = [
        SearchResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content=(
                "系统支持哪些文档格式？"
                "系统支持 PDF、DOCX 和 Markdown 三种文档格式。"
            ),
            score=0.8,
            file_name="formats.md",
            page_no=None,
            section_path=["文档格式"],
            doc_type="article",
            audience="public",
            assessment_code=None,
            assessment_version=None,
            review_status="approved",
        )
    ]

    answer = build_demo_answer(question, sources)

    assert question not in answer
    assert "PDF、DOCX 和 Markdown" in answer
