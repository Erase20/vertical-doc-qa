from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SearchFilters:
    domain: str
    doc_types: tuple[str, ...]
    allowed_access_levels: tuple[str, ...]
    audience: str | None = None
    assessment_code: str | None = None
    assessment_version: str | None = None


@dataclass
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    file_name: str
    page_no: int | None
    section_path: list[str]
    doc_type: str
    audience: str
    assessment_code: str | None
    assessment_version: str | None
    review_status: str


class VectorStore:
    async def search(
        self,
        query_vector: list[float],
        top_k: int,
        knowledge_base_id: str,
        filters: SearchFilters,
    ) -> list[SearchResult]:
        raise NotImplementedError
