"use client";

import { useRef, useState } from "react";
import {
  FileText,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
  Trash2,
  Upload
} from "lucide-react";

import { deleteDocument, reindexDocument, uploadDocument } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";

const PROCESSING_STATUSES = new Set(["uploaded", "parsing", "chunking", "embedding", "retrying"]);

const STATUS_LABELS: Record<string, string> = {
  uploaded: "等待处理",
  parsing: "解析中",
  chunking: "切片中",
  embedding: "向量化",
  retrying: "重试中",
  ready: "可检索",
  failed: "处理失败"
};

interface Props {
  documents: DocumentItem[];
  loading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
}

export function DocumentPanel({ documents, loading, error, onRefresh }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  async function handleUpload(file: File | undefined) {
    if (!file) {
      return;
    }
    setUploading(true);
    setActionError(null);
    try {
      await uploadDocument(file);
      await onRefresh();
    } catch (uploadError) {
      setActionError(uploadError instanceof Error ? uploadError.message : "上传失败");
    } finally {
      setUploading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  async function handleDelete(documentId: string) {
    setActionError(null);
    try {
      await deleteDocument(documentId);
      await onRefresh();
    } catch (deleteError) {
      setActionError(deleteError instanceof Error ? deleteError.message : "删除失败");
    }
  }

  async function handleReindex(documentId: string) {
    setActionError(null);
    try {
      await reindexDocument(documentId);
      await onRefresh();
    } catch (reindexError) {
      setActionError(reindexError instanceof Error ? reindexError.message : "重建失败");
    }
  }

  return (
    <aside className="panel document-panel">
      <div className="panel-header">
        <div className="panel-title">
          <h2>资料库</h2>
          <span>{documents.length}</span>
        </div>
        <button
          className="icon-button"
          type="button"
          aria-label="刷新文档列表"
          title="刷新文档列表"
          onClick={() => void onRefresh()}
        >
          <RefreshCw size={16} />
        </button>
      </div>

      <div className="upload-zone">
        <button
          className="primary-button"
          type="button"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? <LoaderCircle className="processing-spin" size={16} /> : <Upload size={16} />}
          {uploading ? "上传中" : "上传文档"}
        </button>
        <p>PDF、Word 或 Markdown，单个文件不超过 50 MB。</p>
        <input
          ref={inputRef}
          hidden
          type="file"
          accept=".pdf,.docx,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/markdown"
          onChange={(event) => void handleUpload(event.target.files?.[0])}
        />
      </div>

      {(error || actionError) && <div className="error-banner">{actionError ?? error}</div>}

      {loading ? (
        <p className="empty-state">正在加载资料...</p>
      ) : documents.length === 0 ? (
        <p className="empty-state">尚未上传资料</p>
      ) : (
        <ul className="document-list">
          {documents.map((document) => (
            <li className="document-item" key={document.id}>
              <div className="document-heading">
                <FileText size={17} />
                <div>
                  <span className="document-name" title={document.title}>
                    {document.title}
                  </span>
                  <div className="document-meta">
                    {formatFileSize(document.file_size)}
                    {document.chunk_count > 0 ? ` · ${document.chunk_count} 段` : ""}
                  </div>
                </div>
              </div>

              <span className={`status ${document.status}`}>
                {PROCESSING_STATUSES.has(document.status) && (
                  <LoaderCircle className="processing-spin" size={12} />
                )}
                {STATUS_LABELS[document.status] ?? document.status}
              </span>

              {document.error_message && (
                <div className="error-banner" title={document.error_message}>
                  {document.error_code ?? "ERROR"}
                </div>
              )}

              <div className="document-actions">
                <button
                  className="icon-button"
                  type="button"
                  aria-label={`重建 ${document.title}`}
                  title="重建索引"
                  onClick={() => void handleReindex(document.id)}
                >
                  <RotateCcw size={15} />
                </button>
                <button
                  className="icon-button"
                  type="button"
                  aria-label={`删除 ${document.title}`}
                  title="删除文档"
                  onClick={() => void handleDelete(document.id)}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

