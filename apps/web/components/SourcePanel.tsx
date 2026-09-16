"use client";

import { BookOpenText } from "lucide-react";

import type { SourceItem } from "@/lib/types";

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

