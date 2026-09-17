from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk
from app.vectorstores.base import SearchFilters, SearchResult, VectorStore


class PgVectorStore(VectorStore):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(
        self,
        query_vector: list[float],
        top_k: int,
        knowledge_base_id: str,
        filters: SearchFilters,
    ) -> list[SearchResult]:
        distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
        conditions = [
            DocumentChunk.knowledge_base_id == knowledge_base_id,
            Document.deleted_at.is_(None),
            Document.status == "ready",
            Document.domain == filters.domain,
            Document.doc_type.in_(filters.doc_types),
            Document.review_status == "approved",
            Document.access_level.in_(filters.allowed_access_levels),
            DocumentChunk.embedding.is_not(None),
        ]
        if filters.audience:
            conditions.append(Document.audience == filters.audience)
        if filters.assessment_code:
            conditions.append(Document.assessment_code == filters.assessment_code)
        if filters.assessment_version:
            conditions.append(Document.assessment_version == filters.assessment_version)

        statement = (
            select(DocumentChunk, Document, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(*conditions)
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
                doc_type=document.doc_type,
                audience=document.audience,
                assessment_code=document.assessment_code,
                assessment_version=document.assessment_version,
                review_status=document.review_status,
            )
            for chunk, document, distance_value in rows
        ]
