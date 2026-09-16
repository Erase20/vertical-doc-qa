"use client";

import { useCallback, useEffect, useState } from "react";
import { Database, FileText } from "lucide-react";

import { ChatPanel } from "@/components/ChatPanel";
import { DocumentPanel } from "@/components/DocumentPanel";
import { SourcePanel } from "@/components/SourcePanel";
import { listDocuments } from "@/lib/api";
import type { DocumentItem, SourceItem } from "@/lib/types";

export default function HomePage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [activeSource, setActiveSource] = useState<string | null>(null);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [documentError, setDocumentError] = useState<string | null>(null);

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

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">
            <Database size={18} />
          </span>
          <div>
            <strong>文档问答助手</strong>
            <span>垂直知识库工作台</span>
          </div>
        </div>
        <div className="system-summary" aria-label="知识库摘要">
          <span>
            <FileText size={15} />
            {documents.length} 份资料
          </span>
          <span className="summary-ready">{readyCount} 份可检索</span>
        </div>
      </header>

      <div className="workspace">
        <DocumentPanel
          documents={documents}
          loading={loadingDocuments}
          error={documentError}
          onRefresh={refreshDocuments}
        />
        <ChatPanel
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

