from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.vectorstores.base import VectorStore
from app.vectorstores.pgvector import PgVectorStore


def get_vector_store(db: AsyncSession) -> VectorStore:
    if settings.vector_store == "pgvector":
        return PgVectorStore(db)
    raise NotImplementedError(
        "The Chroma adapter is reserved by the interface but is not enabled "
        "in the initial framework."
    )
