from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Document
from app.schemas.api import DocumentList, DocumentRead, DocumentUploadResponse
from app.services.storage import StorageError, remove_file, save_upload
from app.tasks.documents import process_document

router = APIRouter()


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: str = Form(default="default", min_length=1, max_length=64),
    title: str | None = Form(default=None, max_length=255),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    try:
        stored = await save_upload(file)
    except StorageError as exc:
        code = "FILE_TOO_LARGE" if str(exc).startswith("File exceeds") else "INVALID_FILE"
        status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if code == "FILE_TOO_LARGE" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"code": code, "message": str(exc)},
        ) from exc

    existing = await db.scalar(
        select(Document).where(
            Document.knowledge_base_id == knowledge_base_id,
            Document.sha256 == stored.sha256,
            Document.deleted_at.is_(None),
        )
    )
    if existing is not None:
        stored.path.unlink(missing_ok=True)
        return DocumentUploadResponse.model_validate(existing).model_copy(
            update={"duplicate": True}
        )

    document = Document(
        knowledge_base_id=knowledge_base_id,
        title=(title or file.filename or stored.path.name).strip(),
        file_name=file.filename or stored.path.name,
        file_ext=stored.extension,
        mime_type=file.content_type or "application/octet-stream",
        file_size=stored.size,
        storage_path=str(stored.path),
        sha256=stored.sha256,
        status="uploaded",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    process_document.delay(str(document.id))
    return DocumentUploadResponse.model_validate(document)


@router.get("", response_model=DocumentList)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    knowledge_base_id: str | None = Query(default=None),
    document_status: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> DocumentList:
    filters = [Document.deleted_at.is_(None)]
    if knowledge_base_id:
        filters.append(Document.knowledge_base_id == knowledge_base_id)
    if document_status:
        filters.append(Document.status == document_status)

    total = await db.scalar(select(func.count()).select_from(Document).where(*filters))
    result = await db.scalars(
        select(Document)
        .where(*filters)
        .order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return DocumentList(
        items=[DocumentRead.model_validate(item) for item in result],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentRead:
    document = await _get_active_document(db, document_id)
    return DocumentRead.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    document = await _get_active_document(db, document_id)
    storage_path = document.storage_path
    await db.delete(document)
    await db.commit()
    remove_file(storage_path)


@router.post(
    "/{document_id}/reindex",
    response_model=DocumentRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def reindex_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentRead:
    document = await _get_active_document(db, document_id)
    document.status = "uploaded"
    document.error_code = None
    document.error_message = None
    await db.commit()
    await db.refresh(document)
    process_document.delay(str(document.id))
    return DocumentRead.model_validate(document)


async def _get_active_document(db: AsyncSession, document_id: UUID) -> Document:
    document = await db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None),
        )
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    return document
