import type { QueryResponse, QuerySuggestion } from "../api/types";
import { AnswerMarkdown } from "./AnswerMarkdown";
import { CitationList } from "./CitationList";
// (Deep dive opens scoped queries; no direct text-jump link in UI.)

interface QueryPaneProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: () => void;
  loading: boolean;
  hideInput?: boolean;
  result: QueryResponse | null;
  error: string | null;
  selectedIndex: number | null;
  onCitationClick: (index: number, chunkId: string) => void;
  onCitationVerify?: (index: number, chunkId: string) => void;
  verifyingId?: string | null;
  verifyError?: string | null;
  clarificationActive?: boolean;
  onClearClarification?: () => void;
  sourcePreview?: React.ReactNode;
  askedQuery?: string | null;
  suggestions: QuerySuggestion[];
  onSuggestionClick: (query: string, documentId?: string | null) => void;
}

function FollowUpSuggestions({
  items,
  onSuggestionClick,
}: {
  items: QuerySuggestion[];
  onSuggestionClick: (query: string, documentId?: string | null) => void;
}) {
  if (items.length === 0) return null;
  return (
    <div className="suggestions follow-ups" data-testid="follow-up-suggestions">
      <p className="suggestions-label">You might like</p>
      {items.map((s) => (
        <button
          key={s.chunk_id}
          type="button"
          className="btn-suggestion"
          onClick={() => onSuggestionClick(s.query, s.document_id ?? null)}
          data-testid={`follow-up-${s.chunk_id}`}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}

export function QueryPane({
  query,
  onQueryChange,
  onSubmit,
  loading,
  result,
  error,
  selectedIndex,
  onCitationClick,
  onCitationVerify,
  verifyingId = null,
  verifyError = null,
  clarificationActive = false,
  onClearClarification,
  sourcePreview = null,
  askedQuery = null,
  suggestions,
  onSuggestionClick,
  hideInput = false,
}: QueryPaneProps) {
  const followUps = result?.suggested_queries ?? [];
  const outOfCorpusSuggestions =
    result?.out_of_corpus && followUps.length > 0 ? followUps : suggestions;
  const inCorpusFollowUps = result && !result.out_of_corpus ? followUps : [];

  return (
    <section className="conversation-pane" aria-label="Answer and verification">
      {!hideInput && (
        <>
          <textarea
            className="query-input query-input--legacy"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Ask anything…"
            rows={2}
            data-testid="query-input-legacy"
            aria-label="Question"
          />
          <button
            type="button"
            className="btn-primary"
            onClick={onSubmit}
            disabled={loading || !query.trim()}
            data-testid="btn-submit-query-legacy"
            aria-busy={loading}
          >
            {loading ? "Working…" : "Ask"}
          </button>
        </>
      )}

      {clarificationActive && onClearClarification && (
        <button
          type="button"
          className="btn-clear-clarification"
          onClick={onClearClarification}
          data-testid="btn-clear-clarification"
        >
          Start a new question (skip clarification retry)
        </button>
      )}

      {loading && (
        <p className="loading loading-hint" role="status" data-testid="query-loading">
          {result
            ? "Loading answer for the selected article…"
            : "Searching indexed sources and drafting an answer (usually 5–15 seconds)…"}
        </p>
      )}

      {error && (
        <p className="error" role="alert" data-testid="query-error">
          {error}
        </p>
      )}

      {result && (
        <div className="result-block" data-testid="query-result">
          {askedQuery && !result.out_of_corpus && !result.needs_clarification ? (
            <div className="asked-query" data-testid="asked-query">
              <p className="asked-query-label">You asked</p>
              <p className="asked-query-text">{askedQuery}</p>
            </div>
          ) : null}
          {result.out_of_corpus ? (
            <div className="pinky-block" data-testid="pinky-promise">
              <p className="pinky-text">{result.answer.split("\n\n")[0]}</p>
              <FollowUpSuggestions
                items={outOfCorpusSuggestions}
                onSuggestionClick={onSuggestionClick}
              />
            </div>
          ) : result.needs_clarification || result.model_used === "clarification" ? (
            <div className="clarification-block" data-testid="clarification-needed">
              <AnswerMarkdown
                answer={result.answer}
                onCitationClick={() => {}}
                selectedIndex={null}
              />
              <FollowUpSuggestions
                items={inCorpusFollowUps.length > 0 ? inCorpusFollowUps : suggestions.slice(0, 2)}
                onSuggestionClick={onSuggestionClick}
              />
            </div>
          ) : (
            <>
              <FollowUpSuggestions
                items={inCorpusFollowUps.slice(0, 3)}
                onSuggestionClick={onSuggestionClick}
              />

              <AnswerMarkdown
                answer={result.answer}
                onCitationClick={(idx) => {
                  const c = result.citations.find((x) => x.index === idx);
                  if (c) onCitationClick(idx, c.chunk_id);
                }}
                selectedIndex={selectedIndex}
              />

              <CitationList
                citations={result.citations ?? []}
                selectedIndex={selectedIndex}
                onSelect={onCitationClick}
                onVerify={onCitationVerify}
                verifyingId={verifyingId}
              />

              {verifyError && (
                <p className="error" role="alert" data-testid="verify-error">
                  {verifyError}
                </p>
              )}

              {sourcePreview}
            </>
          )}
        </div>
      )}
    </section>
  );
}
