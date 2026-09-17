"use client";

import { useCallback, useEffect, useState } from "react";
import { Database, FileText } from "lucide-react";

import { ChatPanel } from "@/components/ChatPanel";
import { DocumentPanel } from "@/components/DocumentPanel";
import { ModeTabs } from "@/components/ModeTabs";
import { RetrievalFilters } from "@/components/RetrievalFilters";
import { SourcePanel } from "@/components/SourcePanel";
import { listDocuments } from "@/lib/api";
import type {
  DomainMode,
  DocumentItem,
  RetrievalFilters as Filters,
  SourceItem
} from "@/lib/types";

const DEFAULT_FILTERS: Record<DomainMode, Filters> = {
  psychoeducation: { doc_type: "article" },
  assessment: { doc_type: "scale_manual" },
  professional: { doc_type: "paper" }
};

export default function HomePage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [activeSource, setActiveSource] = useState<string | null>(null);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [documentError, setDocumentError] = useState<string | null>(null);
  const [mode, setMode] = useState<DomainMode>("psychoeducation");
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS.psychoeducation);

  const refreshDocuments = useCallback(async () => {
    try {
      const response = await listDocuments();
      setDocuments(response.items);
      setDocumentError(null);
    } catch (error) {
      setDocumentError(error instanceof Error ? error.message : "加载文档失败");
    } finally {
      setLoadingDocuments(false);
    }
  }, []);

  useEffect(() => {
    void refreshDocuments();
    const timer = window.setInterval(() => {
      void refreshDocuments();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [refreshDocuments]);

  const readyCount = documents.filter((document) => document.status === "ready").length;

  function handleModeChange(nextMode: DomainMode) {
    setMode(nextMode);
    setFilters(DEFAULT_FILTERS[nextMode]);
    setSources([]);
    setActiveSource(null);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">
            <Database size={18} />
          </span>
          <div>
            <strong>心理知识工作台</strong>
            <span>科普 · 测评 · 专业资料</span>
          </div>
        </div>
        <ModeTabs mode={mode} onChange={handleModeChange} />
        <div className="system-summary" aria-label="知识库摘要">
          <span>
            <FileText size={15} />
            {documents.length} 份资料
          </span>
          <span className="summary-ready">{readyCount} 份可检索</span>
        </div>
      </header>

      <div className="domain-toolbar">
        <RetrievalFilters mode={mode} value={filters} onChange={setFilters} />
      </div>

      <div className="workspace">
        <DocumentPanel
          documents={documents}
          loading={loadingDocuments}
          error={documentError}
          onRefresh={refreshDocuments}
        />
        <ChatPanel
          mode={mode}
          filters={filters}
          onSources={(nextSources) => {
            setSources(nextSources);
            setActiveSource(nextSources[0]?.id ?? null);
          }}
          onCitation={setActiveSource}
        />
        <SourcePanel
          sources={sources}
          activeSource={activeSource}
          onSelect={setActiveSource}
        />
      </div>
    </main>
  );
}
