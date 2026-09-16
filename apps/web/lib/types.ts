export type DocumentStatus =
  | "uploaded"
  | "parsing"
  | "chunking"
  | "embedding"
  | "retrying"
  | "ready"
  | "failed";

export interface DocumentItem {
  id: string;
  knowledge_base_id: string;
  title: string;
  file_name: string;
  file_ext: string;
  mime_type: string;
  file_size: number;
  status: DocumentStatus;
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
}

export interface StreamCallbacks {
  onMeta?: (data: { request_id: string; conversation_id: string | null }) => void;
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
  onDone?: (data: { message_id: string | null; finish_reason: string; total_ms: number }) => void;
  onError?: (error: { code: string; message: string; retryable: boolean }) => void;
}

