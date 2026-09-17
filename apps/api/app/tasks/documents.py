import asyncio
import hashlib
from pathlib import Path

from sqlalchemy import delete, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Document, DocumentChunk
from app.services.chunking import split_blocks
from app.services.embedding import EmbeddingNotConfigured, get_embedding_client
from app.services.parsing import parse_document
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=5, default_retry_delay=10)
def process_document(self, document_id: str) -> None:
    try:
        asyncio.run(_process_document(document_id))
    except Exception as exc:
        raise self.retry(exc=exc) from exc


async def _process_document(document_id: str) -> None:
    async with SessionLocal() as db:
        document = await db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.deleted_at.is_(None),
            )
        )
        if document is None:
            return

        try:
            document.status = "parsing"
            document.error_code = None
            document.error_message = None
            await db.commit()

            blocks = parse_document(Path(document.storage_path))
            document.status = "chunking"
            await db.commit()

            chunks = split_blocks(blocks)
            if not chunks:
                raise ValueError("No text content was extracted from the document.")

            document.status = "embedding"
            await db.commit()

            embedding_client = get_embedding_client()
            embeddings: list[list[float]] = []
            for start in range(0, len(chunks), settings.embedding_batch_size):
                batch = chunks[start : start + settings.embedding_batch_size]
                result = await embedding_client.embed([chunk.text for chunk in batch])
                embeddings.extend(result.vectors)

            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        knowledge_base_id=document.knowledge_base_id,
                        chunk_index=index,
                        content=chunk.text,
                        content_hash=hashlib.sha256(chunk.text.encode("utf-8")).hexdigest(),
                        token_count=chunk.token_count,
                        page_no=chunk.page_no,
                        section_path=chunk.section_path,
                        paragraph_index=chunk.paragraph_index,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                        embedding=embedding,
                    )
                )

            document.chunk_count = len(chunks)
            document.status = "ready"
            document.error_code = None
            document.error_message = None
            await db.commit()
        except EmbeddingNotConfigured as exc:
            document.status = "failed"
            document.error_code = "MODEL_NOT_CONFIGURED"
            document.error_message = str(exc)
            await db.commit()
            return
        except Exception as exc:
            document.status = "failed"
            document.error_code = "DOCUMENT_PROCESSING_FAILED"
            document.error_message = str(exc)[:1000]
            await db.commit()
            raise
