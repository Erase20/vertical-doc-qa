from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk
from app.vectorstores.base import SearchResult, VectorStore


class PgVectorStore(VectorStore):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(
        self,
        query_vector: list[float],
        top_k: int,
        knowledge_base_id: str,
    ) -> list[SearchResult]:
        distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
        statement = (
            select(DocumentChunk, Document, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                DocumentChunk.knowledge_base_id == knowledge_base_id,
                Document.deleted_at.is_(None),
                Document.status == "ready",
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(top_k)
        )
        rows = (await self.db.execute(statement)).all()
        return [
            SearchResult(
                chunk_id=chunk.id,
                document_id=document.id,
                content=chunk.content,
                score=1.0 - float(distance_value),
                file_name=document.file_name,
                page_no=chunk.page_no,
                section_path=chunk.section_path,
            )
            for chunk, document, distance_value in rows
        ]

