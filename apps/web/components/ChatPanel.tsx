"use client";

import { FormEvent, KeyboardEvent, useRef, useState } from "react";
import { MessageSquareText, Send, Square } from "lucide-react";

import { streamChat } from "@/lib/api";
import type { ChatMessage, SourceItem } from "@/lib/types";

interface Props {
  onSources: (sources: SourceItem[]) => void;
  onCitation: (sourceId: string) => void;
}

export function ChatPanel({ onSources, onCitation }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const conversationId = useRef<string | null>(null);
  const abortController = useRef<AbortController | null>(null);
  const messageSequence = useRef(0);

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
    onSources([]);

    const controller = new AbortController();
    abortController.current = controller;

    try {
      await streamChat(
        {
          question: normalizedQuestion,
          conversation_id: conversationId.current,
          knowledge_base_id: "default"
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
              <h1>询问你的资料</h1>
              <p>上传并完成索引后，答案会附上对应的文档片段。</p>
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
        {error && <div className="error-banner">{error}</div>}
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

