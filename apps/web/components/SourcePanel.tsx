"use client";

import { BookOpenText } from "lucide-react";

import type { Audience, DocumentType, ReviewStatus, SourceItem } from "@/lib/types";

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  article: "科普文章",
  guide: "指南说明",
  scale_manual: "测评手册",
  paper: "研究论文",
  policy: "政策规范",
  reference: "参考资料"
};

const AUDIENCE_LABELS: Record<Audience, string> = {
  public: "公众",
  student: "学生",
  teacher: "教师",
  clinician: "专业人员",
  researcher: "研究人员"
};

const REVIEW_LABELS: Record<ReviewStatus, string> = {
  draft: "草稿",
  reviewed: "已复核",
  approved: "已审核",
  expired: "已过期"
};

interface Props {
  sources: SourceItem[];
  activeSource: string | null;
  onSelect: (sourceId: string) => void;
}

export function SourcePanel({ sources, activeSource, onSelect }: Props) {
  const selected = sources.find((source) => source.id === activeSource) ?? sources[0];

  return (
    <aside className="panel source-panel">
      <div className="panel-header">
        <div className="panel-title">
          <BookOpenText size={17} />
          <h2>来源</h2>
          <span>{sources.length}</span>
        </div>
      </div>

      {sources.length === 0 ? (
        <p className="empty-state">当前回答暂无来源</p>
      ) : (
        <>
          <ul className="source-list">
            {sources.map((source) => (
              <li key={source.id}>
                <button
                  className={`source-item ${source.id === selected?.id ? "active" : ""}`}
                  type="button"
                  onClick={() => onSelect(source.id)}
                >
                  <span className="source-item-head">
                    <span className="source-id">[{source.id}]</span>
                    <span className="source-score">{Math.round(source.score * 100)}%</span>
                  </span>
                  <span className="source-name">{source.name}</span>
                  <span className="source-location">
                    {source.page ? `第 ${source.page} 页` : "无页码"}
                    {source.section ? ` · ${source.section}` : ""}
                  </span>
                  <span className="source-meta">
                    <span>{DOCUMENT_TYPE_LABELS[source.doc_type]}</span>
                    <span>{AUDIENCE_LABELS[source.audience]}</span>
                    {source.assessment_version && (
                      <span>
                        {source.assessment_code} {source.assessment_version}
                      </span>
                    )}
                    <span>{REVIEW_LABELS[source.review_status]}</span>
                  </span>
                  <p className="source-excerpt">{source.excerpt}</p>
                </button>
              </li>
            ))}
          </ul>

          {selected && (
            <div className="source-detail">
              <h3>
                [{selected.id}] {selected.name}
              </h3>
              <p>{selected.excerpt}</p>
            </div>
          )}
        </>
      )}
    </aside>
  );
}
