from dataclasses import dataclass
from uuid import UUID


@dataclass
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    file_name: str
    page_no: int | None
    section_path: list[str]


class VectorStore:
    async def search(
        self,
        query_vector: list[float],
        top_k: int,
        knowledge_base_id: str,
    ) -> list[SearchResult]:
        raise NotImplementedError

