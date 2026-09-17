"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { MessageSquareText, Send, Square } from "lucide-react";

import { SafetyNotice } from "@/components/SafetyNotice";
import { streamChat } from "@/lib/api";
import type {
  ChatMessage,
  DomainMode,
  RetrievalFilters,
  SourceItem
} from "@/lib/types";

interface Props {
  mode: DomainMode;
  filters: RetrievalFilters;
  onSources: (sources: SourceItem[]) => void;
  onCitation: (sourceId: string) => void;
}

const MODE_COPY: Record<DomainMode, { title: string; description: string; limitation: string }> = {
  psychoeducation: {
    title: "了解心理健康知识",
    description: "回答用于心理科普，不用于诊断个人状态。",
    limitation: "内容仅用于健康教育，不能替代专业评估。"
  },
  assessment: {
    title: "查询测评说明",
    description: "结果会尽量标注测评版本、适用人群和计分限制。",
    limitation: "量表分数不能单独作为临床诊断依据。"
  },
  professional: {
    title: "检索专业资料",
    description: "优先使用指南、政策、综述和研究资料。",
    limitation: "请结合证据年份、研究人群和适用边界判断结论。"
  }
};

export function ChatPanel({ mode, filters, onSources, onCitation }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [safetyLevel, setSafetyLevel] = useState<"crisis" | "normal" | null>(null);
  const conversationId = useRef<string | null>(null);
  const abortController = useRef<AbortController | null>(null);
  const messageSequence = useRef(0);
  const modeCopy = MODE_COPY[mode];

  useEffect(() => {
    conversationId.current = null;
    setMessages([]);
    setQuestion("");
    setError(null);
    setSafetyLevel(null);
  }, [mode]);

  async function submitQuestion(event?: FormEvent) {
    event?.preventDefault();
    const normalizedQuestion = question.trim();
    if (!normalizedQuestion || streaming) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${messageSequence.current++}`,
      role: "user",
      content: normalizedQuestion
    };
    const assistantId = `assistant-${messageSequence.current++}`;

    setMessages((current) => [
      ...current,
      userMessage,
      { id: assistantId, role: "assistant", content: "" }
    ]);
    setQuestion("");
    setStreaming(true);
    setError(null);
    setSafetyLevel(null);
    onSources([]);

    const controller = new AbortController();
    abortController.current = controller;

    try {
      await streamChat(
        {
          question: normalizedQuestion,
          conversation_id: conversationId.current,
          knowledge_base_id: "psychology",
          mode,
          filters
        },
        {
          onMeta: (meta) => {
            conversationId.current = meta.conversation_id;
          },
          onSources,
          onToken: (delta) => {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? { ...message, content: message.content + delta }
                  : message
              )
            );
          },
          onError: (streamError) => {
            setError(`${streamError.code}: ${streamError.message}`);
          },
          onSafety: (safety) => {
            setSafetyLevel(safety.level);
          }
        },
        controller.signal
      );
    } catch (streamError) {
      if (!(streamError instanceof DOMException && streamError.name === "AbortError")) {
        setError(streamError instanceof Error ? streamError.message : "请求失败");
      }
    } finally {
      setStreaming(false);
      abortController.current = null;
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitQuestion();
    }
  }

  function stopStreaming() {
    abortController.current?.abort();
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <div className="panel-title">
          <MessageSquareText size={17} />
          <h2>问答</h2>
        </div>
        <span>{streaming ? "生成中" : "就绪"}</span>
      </div>

      <div className="messages" aria-live="polite">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-inner">
              <MessageSquareText size={32} />
              <h1>{modeCopy.title}</h1>
              <p>{modeCopy.description}</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <article className={`message ${message.role}`} key={message.id}>
              <span className="message-role">{message.role === "user" ? "你" : "助手"}</span>
              <div className="message-content">
                {message.role === "assistant" ? (
                  renderAssistantContent(message.content, onCitation)
                ) : (
                  message.content
                )}
              </div>
            </article>
          ))
        )}
      </div>

      <div className="composer-wrap">
        {safetyLevel === "crisis" && <SafetyNotice level={safetyLevel} />}
        {error && <div className="error-banner">{error}</div>}
        <p className="answer-limitation">{modeCopy.limitation}</p>
        <form className="composer" onSubmit={(event) => void submitQuestion(event)}>
          <textarea
            value={question}
            rows={1}
            placeholder="输入你的问题"
            disabled={streaming}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleKeyDown}
          />
          <div className="composer-actions">
            {streaming ? (
              <button
                className="text-button"
                type="button"
                aria-label="停止生成"
                title="停止生成"
                onClick={stopStreaming}
              >
                <Square size={14} />
              </button>
            ) : (
              <button
                className="primary-button"
                type="submit"
                aria-label="发送问题"
                title="发送"
                disabled={!question.trim()}
              >
                <Send size={16} />
              </button>
            )}
          </div>
        </form>
      </div>
    </section>
  );
}

function renderAssistantContent(content: string, onCitation: (sourceId: string) => void) {
  const parts = content.split(/(\[S\d+\])/g);
  return parts.map((part, index) => {
    const match = /^\[(S\d+)\]$/.exec(part);
    if (!match) {
      return <span key={`${part}-${index}`}>{part}</span>;
    }
    return (
      <button
        className="citation-button"
        key={`${part}-${index}`}
        type="button"
        onClick={() => onCitation(match[1])}
      >
        {part}
      </button>
    );
  });
}
