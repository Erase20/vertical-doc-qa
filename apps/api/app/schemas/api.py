from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.domain import (
    Audience,
    DocumentType,
    DomainMode,
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
    redis: str
    vector_store: str
    model_configured: bool
    model_mode: Literal["demo", "live"]


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    knowledge_base_id: str
    title: str
    file_name: str
    file_ext: str
    mime_type: str
    file_size: int
    status: str
    domain: str
    doc_type: str
    audience: str
    assessment_code: str | None
    assessment_version: str | None
    access_level: str
    review_status: str
    error_code: str | None
    error_message: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    items: list[DocumentRead]
    total: int
    page: int
    page_size: int


class DocumentUploadResponse(DocumentRead):
    duplicate: bool = False


class RetrievalFilters(BaseModel):
    doc_type: DocumentType | None = None
    audience: Audience | None = None
    assessment_code: str | None = Field(default=None, min_length=1, max_length=64)
    assessment_version: str | None = Field(default=None, min_length=1, max_length=32)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    conversation_id: UUID | None = None
    knowledge_base_id: str = Field(default="default", min_length=1, max_length=64)
    mode: DomainMode = "psychoeducation"
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


class SourceRead(BaseModel):
    id: str
    chunk_id: UUID
    document_id: UUID
    name: str
    page: int | None
    section: str | None
    score: float
    excerpt: str
    doc_type: str
    audience: str
    assessment_code: str | None
    assessment_version: str | None
    review_status: str


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    retryable: bool = False


class ErrorResponse(BaseModel):
    error: ErrorBody


class CallMetric(BaseModel):
    request_id: UUID
    operation: Literal["embedding", "chat"]
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    currency: str
    latency_ms: int
    first_token_ms: int | None
    success: bool
    created_at: datetime


class CallMetricList(BaseModel):
    items: list[CallMetric]
    total: int
