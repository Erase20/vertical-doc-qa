import type {
  ChatRequest,
  DocumentItem,
  DocumentListResponse,
  SourceItem,
  StreamCallbacks
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

async function parseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    return payload.detail?.message ?? payload.error?.message ?? payload.detail ?? response.statusText;
  } catch {
    return response.statusText || `Request failed with status ${response.status}`;
  }
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const response = await fetch(`${API_BASE_URL}/documents?page_size=100`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const body = new FormData();
  body.append("file", file);
  body.append("knowledge_base_id", "default");

  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: "POST",
    body
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
}

export async function reindexDocument(documentId: string): Promise<DocumentItem> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/reindex`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function streamChat(
  payload: ChatRequest,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    signal
  });

  if (!response.ok || !response.body) {
    throw new Error(await parseError(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      dispatchFrame(frame, callbacks);
    }

    if (done) {
      if (buffer.trim()) {
        dispatchFrame(buffer, callbacks);
      }
      break;
    }
  }
}

function dispatchFrame(frame: string, callbacks: StreamCallbacks): void {
  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (!dataLines.length) {
    return;
  }

  const data = JSON.parse(dataLines.join("\n"));
  if (eventName === "meta") {
    callbacks.onMeta?.(data);
  } else if (eventName === "sources") {
    callbacks.onSources?.(data.sources as SourceItem[]);
  } else if (eventName === "token") {
    callbacks.onToken?.(data.delta);
  } else if (eventName === "usage") {
    callbacks.onUsage?.(data);
  } else if (eventName === "done") {
    callbacks.onDone?.(data);
  } else if (eventName === "error") {
    callbacks.onError?.(data);
  }
}

