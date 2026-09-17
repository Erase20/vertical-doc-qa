"use client";

import { SlidersHorizontal } from "lucide-react";

import type {
  Audience,
  DocumentType,
  DomainMode,
  RetrievalFilters as Filters
} from "@/lib/types";

const DOCUMENT_TYPES: Array<{ value: DocumentType; label: string }> = [
  { value: "article", label: "科普文章" },
  { value: "guide", label: "指南说明" },
  { value: "scale_manual", label: "测评手册" },
  { value: "paper", label: "研究论文" },
  { value: "policy", label: "政策规范" }
];

const AUDIENCES: Array<{ value: Audience; label: string }> = [
  { value: "public", label: "公众" },
  { value: "student", label: "学生" },
  { value: "teacher", label: "教师" },
  { value: "clinician", label: "专业人员" },
  { value: "researcher", label: "研究人员" }
];

const DEFAULT_DOC_TYPES: Record<DomainMode, DocumentType | ""> = {
  psychoeducation: "article",
  assessment: "scale_manual",
  professional: "paper"
};

interface Props {
  mode: DomainMode;
  value: Filters;
  onChange: (filters: Filters) => void;
}

export function RetrievalFilters({ mode, value, onChange }: Props) {
  const selectedDocumentType =
    value.doc_type === null ? "" : value.doc_type ?? DEFAULT_DOC_TYPES[mode];

  return (
    <div className="retrieval-filters">
      <span className="filter-title">
        <SlidersHorizontal size={13} />
        筛选
      </span>
      <select
        aria-label="资料类型"
        value={selectedDocumentType}
        onChange={(event) =>
          onChange({
            ...value,
            doc_type: (event.target.value || null) as DocumentType | null
          })
        }
      >
        <option value="">全部类型</option>
        {DOCUMENT_TYPES.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
      <select
        aria-label="适用人群"
        value={value.audience ?? ""}
        onChange={(event) => {
          onChange({
            ...value,
            audience: (event.target.value || null) as Audience | null
          });
        }}
      >
        <option value="">全部人群</option>
        {AUDIENCES.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
      {mode === "assessment" && (
        <>
          <input
            aria-label="测评代码"
            placeholder="测评代码"
            value={value.assessment_code ?? ""}
            onChange={(event) =>
              onChange({
                ...value,
                assessment_code: event.target.value || null
              })
            }
          />
          <input
            aria-label="测评版本"
            placeholder="版本"
            value={value.assessment_version ?? ""}
            onChange={(event) =>
              onChange({
                ...value,
                assessment_version: event.target.value || null
              })
            }
          />
        </>
      )}
    </div>
  );
}
