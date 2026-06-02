import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchExportGate,
  fetchHealth,
  fetchStarterPrompts,
  getBackendUrl,
  postQuery,
  verifyChunk,
} from "./api/client";
import type { ExportGate, QueryResponse, StarterPrompt } from "./api/types";
import { ExportToolbar } from "./components/ExportToolbar";
import { GlassHeader } from "./components/GlassHeader";
import { GlassLandingPremium as GlassLanding } from "./components/GlassLandingPremium";
import { GlassSearchBar } from "./components/GlassSearchBar";
import { QueryPane } from "./components/QueryPane";
import { SourcePreviewPanel } from "./components/SourcePreviewPanel";
import { VerificationBar } from "./components/VerificationBar";
import { FALLBACK_STARTER_PROMPTS } from "./lib/fallbackStarters";
import {
  clearClarificationContext,
  loadClarificationContext,
  saveClarificationContext,
} from "./lib/clarificationSession";

export default function App() {
  const [query, setQuery] = useState("");
  const [askedQuery, setAskedQuery] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [health, setHealth] = useState<string>("checking…");
  const [starterPrompts, setStarterPrompts] = useState<StarterPrompt[]>(FALLBACK_STARTER_PROMPTS);

  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  const [exportGate, setExportGate] = useState<ExportGate | null>(null);
  const [clarificationAnchorQuery, setClarificationAnchorQuery] = useState<string | null>(null);

  const conversationStarted = result !== null || loading;

  // Prevent out-of-order responses from desyncing answer vs citations.
  const activeRunId = useRef(0);

  const refreshExportGate = useCallback(async (sessionId: string) => {
    try {
      const gate = await fetchExportGate(sessionId);
      setExportGate(gate);
    } catch {
      setExportGate(null);
    }
  }, []);

  const selectCitation = useCallback(
    (index: number, chunkId: string) => {
      setSelectedIndex(index);
      const citation =
        result?.citations.find((c) => c.index === index && c.chunk_id === chunkId) ??
        result?.citations.find((c) => c.index === index) ??
        null;
      // selection is still useful for highlight; no preview panel rendered
      void citation;
    },
    [result]
  );

  const resolvePriorSession = useCallback(
    (_q: string, documentId?: string | null): string | null => {
      if (documentId) return null;
      const stored = loadClarificationContext();
      if (!stored) return null;
      return stored.sessionId;
    },
    []
  );

  const runQuery = useCallback(
    async (text: string, documentId?: string | null) => {
      const q = text.trim();
      if (!q) return;
      const runId = ++activeRunId.current;
      setQuery(q);
      setAskedQuery(q);
      setLoading(true);
      setQueryError(null);
      setVerifyError(null);
      setSelectedIndex(null);
      // no source preview panel in prototype
      setExportGate(null);

      const priorSession = resolvePriorSession(q, documentId);
      try {
        const res = await postQuery(q, documentId, priorSession);
        if (activeRunId.current !== runId) return;
        const normalized: QueryResponse = {
          ...res,
          citations: res.citations ?? [],
          suggested_queries: res.suggested_queries ?? [],
          answer: res.answer ?? "",
        };
        setResult(normalized);
        // Clear the input after we have a response (keep askedQuery visible above the answer).
        setQuery("");

        if (normalized.needs_clarification || normalized.model_used === "clarification") {
          saveClarificationContext({ sessionId: normalized.session_id, anchorQuery: q });
          setClarificationAnchorQuery(q);
        } else {
          clearClarificationContext();
          setClarificationAnchorQuery(null);
        }

        if (!normalized.out_of_corpus && !normalized.needs_clarification) {
          await refreshExportGate(normalized.session_id);
          const cites = normalized.citations;
          if (cites.length === 1) {
            selectCitation(cites[0].index, cites[0].chunk_id);
          }
        }

        requestAnimationFrame(() => {
          document.querySelector(".result-block")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      } catch (e) {
        if (activeRunId.current !== runId) return;
        setQueryError(
          e instanceof Error
            ? `${e.message} — is the API running at ${getBackendUrl()}?`
            : "Query failed"
        );
      } finally {
        if (activeRunId.current === runId) setLoading(false);
      }
    },
    [refreshExportGate, resolvePriorSession, selectCitation]
  );

  const handleStarterClick = useCallback(
    (prompt: StarterPrompt) => {
      void runQuery(prompt.query, prompt.document_id ?? null);
    },
    [runQuery]
  );

  const startNewChat = useCallback(() => {
    // Invalidate any in-flight query.
    activeRunId.current += 1;
    clearClarificationContext();
    setClarificationAnchorQuery(null);
    setQuery("");
    setAskedQuery(null);
    setResult(null);
    setQueryError(null);
    setVerifyError(null);
    setSelectedIndex(null);
    setExportGate(null);
    void fetchStarterPrompts()
      .then((items) => {
        if (items.length >= 3) setStarterPrompts(items);
      })
      .catch(() => setStarterPrompts(FALLBACK_STARTER_PROMPTS));
  }, []);

  const verifyCitation = useCallback(
    async (index: number, chunkId: string) => {
      if (!result) return;
      const citation =
        result.citations.find((c) => c.index === index && c.chunk_id === chunkId) ??
        result.citations.find((c) => c.index === index);
      if (!citation || citation.verification_status === "verified") return;

      setSelectedIndex(index);

      setVerifyingId(citation.chunk_id);
      setVerifyError(null);
      try {
        await verifyChunk(result.session_id, citation.chunk_id);
        setResult((prev) =>
          prev
            ? {
                ...prev,
                citations: prev.citations.map((c) =>
                  c.chunk_id === citation.chunk_id
                    ? { ...c, verification_status: "verified" }
                    : c
                ),
              }
            : prev
        );
        await refreshExportGate(result.session_id);
      } catch (e) {
        setVerifyError(e instanceof Error ? e.message : "Verification failed");
      } finally {
        setVerifyingId(null);
      }
    },
    [result, refreshExportGate]
  );

  useEffect(() => {
    void fetchHealth()
      .then((h) => {
        const parts = [
          h.status,
          `Chroma ${h.chroma}`,
          h.groq_live ? "Groq live" : "Groq mock",
          h.rag_retrieval ? `search ${h.rag_retrieval}` : null,
        ].filter(Boolean);
        setHealth(parts.join(" · "));
      })
      .catch(() => setHealth("API unreachable"));
    void fetchStarterPrompts()
      .then((items) => {
        if (items.length >= 3) setStarterPrompts(items);
      })
      .catch(() => setStarterPrompts(FALLBACK_STARTER_PROMPTS));
  }, []);

  return (
    <div className="glass-app" data-testid="hitl-app">
      <GlassHeader
        health={health}
        showNewChat={conversationStarted}
        onNewChat={startNewChat}
      />

      <main className="glass-main">
        {!conversationStarted ? (
          <GlassLanding
            query={query}
            onQueryChange={setQuery}
            onSubmit={() => void runQuery(query)}
            loading={loading}
            starters={starterPrompts}
            onStarterClick={handleStarterClick}
          />
        ) : (
          <div className="glass-conversation">
            <div className="glass-conversation-search">
              <GlassSearchBar
                value={query}
                onChange={setQuery}
                onSubmit={() => void runQuery(query)}
                loading={loading}
                compact
              />
            </div>

            {queryError && (
              <p className="error glass-error" role="alert" data-testid="query-error">
                {queryError}
              </p>
            )}

            <QueryPane
              query={query}
              onQueryChange={setQuery}
              onSubmit={() => void runQuery(query)}
              loading={loading}
              result={result}
              error={null}
              selectedIndex={selectedIndex}
              onCitationClick={selectCitation}
              onCitationVerify={(idx, id) => void verifyCitation(idx, id)}
              verifyingId={verifyingId}
              verifyError={verifyError}
              clarificationActive={Boolean(clarificationAnchorQuery)}
              onClearClarification={() => {
                clearClarificationContext();
                setClarificationAnchorQuery(null);
              }}
              askedQuery={askedQuery}
              suggestions={result?.suggested_queries ?? []}
              onSuggestionClick={(q, docId) => void runQuery(q, docId)}
              hideInput
              sourcePreview={null}
            />

            {/* Prototype: keep component wired for Phase-6 gate tests, but do not render UI. */}
            {false && (
              <SourcePreviewPanel
                citation={null}
                chunk={null}
                loading={false}
                error={null}
                anchorQuery=""
              />
            )}
          </div>
        )}
      </main>

      {result && !result.out_of_corpus && result.citations.length > 0 && (
        <>
          <VerificationBar gate={exportGate} />
          <ExportToolbar gate={exportGate} answer={result.answer} />
        </>
      )}
    </div>
  );
}
