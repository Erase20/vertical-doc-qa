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
import type {
  AccessLevel,
  Audience,
  DocumentDomain,
  DocumentItem,
  DocumentType,
  ReviewStatus
} from "@/lib/types";

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

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  article: "科普文章",
  guide: "指南说明",
  scale_manual: "测评手册",
  paper: "研究论文",
  policy: "政策规范",
  reference: "参考资料"
};

const DOMAIN_LABELS: Record<DocumentDomain, string> = {
  general: "通用",
  psychoeducation: "心理科普",
  assessment: "测评说明",
  professional: "专业资料"
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
  const [domain, setDomain] = useState<DocumentDomain>("psychoeducation");
  const [docType, setDocType] = useState<DocumentType>("article");
  const [audience, setAudience] = useState<Audience>("public");
  const [assessmentCode, setAssessmentCode] = useState("");
  const [assessmentVersion, setAssessmentVersion] = useState("");
  const [accessLevel, setAccessLevel] = useState<AccessLevel>("public");
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>("approved");

  async function handleUpload(file: File | undefined) {
    if (!file) {
      return;
    }
    setUploading(true);
    setActionError(null);
    try {
      if (domain === "assessment" && (!assessmentCode.trim() || !assessmentVersion.trim())) {
        throw new Error("测评资料必须填写测评代码和版本。");
      }
      await uploadDocument(file, {
        knowledge_base_id: "psychology",
        domain,
        doc_type: docType,
        audience,
        assessment_code: assessmentCode.trim() || undefined,
        assessment_version: assessmentVersion.trim() || undefined,
        access_level: accessLevel,
        review_status: reviewStatus
      });
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

  function handleDomainChange(nextDomain: DocumentDomain) {
    setDomain(nextDomain);
    if (nextDomain === "assessment") {
      setDocType("scale_manual");
      setAudience("clinician");
      setAccessLevel("professional_only");
    } else if (nextDomain === "professional") {
      setDocType("paper");
      setAudience("researcher");
      setAccessLevel("professional_only");
    } else {
      setDocType("article");
      setAudience("public");
      setAccessLevel("public");
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
        <div className="upload-fields">
          <label>
            <span>资料领域</span>
            <select
              value={domain}
              onChange={(event) => handleDomainChange(event.target.value as DocumentDomain)}
            >
              <option value="psychoeducation">心理科普</option>
              <option value="assessment">测评说明</option>
              <option value="professional">专业资料</option>
            </select>
          </label>
          <label>
            <span>资料类型</span>
            <select
              value={docType}
              onChange={(event) => setDocType(event.target.value as DocumentType)}
            >
              {Object.entries(DOCUMENT_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>适用人群</span>
            <select
              value={audience}
              onChange={(event) => setAudience(event.target.value as Audience)}
            >
              <option value="public">公众</option>
              <option value="student">学生</option>
              <option value="teacher">教师</option>
              <option value="clinician">专业人员</option>
              <option value="researcher">研究人员</option>
            </select>
          </label>
          {domain === "assessment" && (
            <>
              <label>
                <span>测评代码</span>
                <input
                  value={assessmentCode}
                  placeholder="例如 DEMO-9"
                  onChange={(event) => setAssessmentCode(event.target.value)}
                />
              </label>
              <label>
                <span>测评版本</span>
                <input
                  value={assessmentVersion}
                  placeholder="例如 2026"
                  onChange={(event) => setAssessmentVersion(event.target.value)}
                />
              </label>
            </>
          )}
          <label>
            <span>访问级别</span>
            <select
              value={accessLevel}
              onChange={(event) => setAccessLevel(event.target.value as AccessLevel)}
            >
              <option value="public">公开</option>
              <option value="restricted">受限</option>
              <option value="professional_only">仅专业人员</option>
            </select>
          </label>
          <label>
            <span>审核状态</span>
            <select
              value={reviewStatus}
              onChange={(event) => setReviewStatus(event.target.value as ReviewStatus)}
            >
              <option value="approved">已审核</option>
              <option value="reviewed">已复核</option>
              <option value="draft">草稿</option>
              <option value="expired">已过期</option>
            </select>
          </label>
        </div>
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
                  <div className="document-meta">
                    {DOMAIN_LABELS[document.domain]} · {DOCUMENT_TYPE_LABELS[document.doc_type]}
                    {document.assessment_version
                      ? ` · ${document.assessment_code} ${document.assessment_version}`
                      : ""}
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
