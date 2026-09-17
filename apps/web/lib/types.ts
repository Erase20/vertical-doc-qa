export type DocumentStatus =
  | "uploaded"
  | "parsing"
  | "chunking"
  | "embedding"
  | "retrying"
  | "ready"
  | "failed";

export type DomainMode = "psychoeducation" | "assessment" | "professional";
export type DocumentDomain = DomainMode | "general";
export type DocumentType =
  | "article"
  | "guide"
  | "scale_manual"
  | "paper"
  | "policy"
  | "reference";
export type Audience = "public" | "student" | "teacher" | "clinician" | "researcher";
export type AccessLevel = "public" | "restricted" | "professional_only";
export type ReviewStatus = "draft" | "reviewed" | "approved" | "expired";

export interface DocumentItem {
  id: string;
  knowledge_base_id: string;
  title: string;
  file_name: string;
  file_ext: string;
  mime_type: string;
  file_size: number;
  status: DocumentStatus;
  domain: DocumentDomain;
  doc_type: DocumentType;
  audience: Audience;
  assessment_code: string | null;
  assessment_version: string | null;
  access_level: AccessLevel;
  review_status: ReviewStatus;
  error_code: string | null;
  error_message: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface SourceItem {
  id: string;
  chunk_id: string;
  document_id: string;
  name: string;
  page: number | null;
  section: string | null;
  score: number;
  excerpt: string;
  doc_type: DocumentType;
  audience: Audience;
  assessment_code: string | null;
  assessment_version: string | null;
  review_status: ReviewStatus;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  question: string;
  conversation_id?: string | null;
  knowledge_base_id?: string;
  mode: DomainMode;
  filters: RetrievalFilters;
}

export interface RetrievalFilters {
  doc_type?: DocumentType | null;
  audience?: Audience | null;
  assessment_code?: string | null;
  assessment_version?: string | null;
}

export interface DocumentUploadMetadata {
  knowledge_base_id: string;
  domain: DocumentDomain;
  doc_type: DocumentType;
  audience: Audience;
  assessment_code?: string;
  assessment_version?: string;
  access_level: AccessLevel;
  review_status: ReviewStatus;
}

export interface StreamCallbacks {
  onMeta?: (data: {
    request_id: string;
    conversation_id: string | null;
    mode: DomainMode;
  }) => void;
  onSources?: (sources: SourceItem[]) => void;
  onToken?: (delta: string) => void;
  onUsage?: (usage: {
    input_tokens: number;
    output_tokens: number;
    embedding_tokens: number;
    cost: number;
    currency: string;
    is_estimated: boolean;
  }) => void;
  onDone?: (data: {
    message_id: string | null;
    finish_reason: string;
    total_ms: number;
    mode?: DomainMode;
  }) => void;
  onSafety?: (data: {
    level: "crisis" | "normal";
    action: string;
    request_id: string;
  }) => void;
  onError?: (error: { code: string; message: string; retryable: boolean }) => void;
}
