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
        )
    ]

    answer = build_demo_answer("系统使用什么存储向量？", sources)

    assert "PostgreSQL" in answer
    assert "[S1]" in answer
