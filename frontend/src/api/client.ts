import type {
  ChunkDetail,
  ExportGate,
  HealthResponse,
  QueryResponse,
  QuerySuggestion,
  StarterPrompt,
} from "./types";

const QUERY_TIMEOUT_MS = 90_000;

function backendBase(): string {
  // Dev: always use Vite proxy (same origin) — avoids CORS and wrong ports
  if (import.meta.env.DEV) {
    return "";
  }
  const fromEnv =
    import.meta.env.VITE_BACKEND_URL ?? import.meta.env.NEXT_PUBLIC_BACKEND_URL;
  if (fromEnv) {
    return String(fromEnv).replace(/\/$/, "");
  }
  return "http://127.0.0.1:8000";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), QUERY_TIMEOUT_MS);
  try {
    const res = await fetch(`${backendBase()}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }
    return res.json() as Promise<T>;
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error(
        "Request timed out — the server may be busy. Check that the API is running on port 8000."
      );
    }
    throw e;
  } finally {
    window.clearTimeout(timeout);
  }
}

export function getBackendUrl(): string {
  return backendBase() || "(Vite proxy → port 8000)";
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function postQuery(
  query: string,
  documentId?: string | null,
  priorSessionId?: string | null
): Promise<QueryResponse> {
  const body: { query: string; document_id?: string; prior_session_id?: string } = {
    query,
  };
  if (documentId) {
    body.document_id = documentId;
  }
  if (priorSessionId) {
    body.prior_session_id = priorSessionId;
  }
  return request<QueryResponse>("/api/v1/query", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchChunk(chunkId: string): Promise<ChunkDetail> {
  return request<ChunkDetail>(`/api/v1/chunks/${encodeURIComponent(chunkId)}`);
}

export async function verifyChunk(
  sessionId: string,
  chunkId: string,
  verified = true
): Promise<void> {
  await request(`/api/v1/sessions/${sessionId}/verify/${encodeURIComponent(chunkId)}`, {
    method: "PATCH",
    body: JSON.stringify({ verified }),
  });
}

export async function fetchExportGate(sessionId: string): Promise<ExportGate> {
  return request<ExportGate>(
    `/api/v1/sessions/${encodeURIComponent(sessionId)}/export-gate`
  );
}

export async function fetchSuggestions(): Promise<QuerySuggestion[]> {
  return request<QuerySuggestion[]>("/api/v1/suggestions");
}

export async function fetchStarterPrompts(): Promise<StarterPrompt[]> {
  // Cache-bust so each "New chat" gets fresh prompts even with aggressive caching.
  return request<StarterPrompt[]>(`/api/v1/starter-prompts?t=${Date.now()}`);
}
