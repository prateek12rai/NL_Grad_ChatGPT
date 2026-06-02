import type { Citation } from "../api/types";

interface CitationListProps {
  citations: Citation[];
  selectedIndex: number | null;
  onSelect: (index: number, chunkId: string) => void;
  onVerify?: (index: number, chunkId: string) => void;
  verifyingId?: string | null;
}

export function CitationList({
  citations,
  selectedIndex,
  onSelect,
  onVerify,
  verifyingId = null,
}: CitationListProps) {
  if (citations.length === 0) return null;

  return (
    <ul className="citation-matrix" data-testid="citation-matrix" aria-label="Source citations">
      {citations.map((c) => {
        const verified = c.verification_status === "verified";
        const busy = verifyingId === c.chunk_id;
        return (
          <li key={c.chunk_id}>
            <div
              className={`citation-row ${selectedIndex === c.index ? "selected" : ""} ${
                verified ? "verified" : "unverified"
              }`}
              data-testid={`citation-row-${c.index}`}
            >
              <button
                type="button"
                className="citation-row-main"
                onClick={() => onSelect(c.index, c.chunk_id)}
                aria-label={`Highlight source ${c.index}`}
              >
                <span className="cite-num">[{c.index}]</span>
                <span className="cite-title">{c.document_title}</span>
                {c.publication_date && (
                  <span className="cite-date">{c.publication_date}</span>
                )}
              </button>

              {c.source_url && (
                <button
                  type="button"
                  className="cite-open-link"
                  onClick={(e) => {
                    e.stopPropagation();
                    window.open(c.source_url!, "_blank", "noopener,noreferrer");
                  }}
                  aria-label={`Open source article for citation ${c.index}`}
                >
                  Open article
                </button>
              )}

              {verified ? (
                <span
                  className="cite-nudge cite-nudge--done"
                  data-testid={`cite-verified-${c.index}`}
                  aria-label={`Source ${c.index} verified`}
                >
                  <span className="cite-nudge-emoji" aria-hidden="true">😎</span>
                  Verified!
                </span>
              ) : (
                <button
                  type="button"
                  className={`cite-nudge cite-nudge--ask ${busy ? "is-busy" : ""}`}
                  disabled={busy || !onVerify}
                  onClick={(e) => {
                    e.stopPropagation();
                    onVerify?.(c.index, c.chunk_id);
                  }}
                  title="Review the article excerpt above, then click Verify to unlock export"
                  data-testid={`cite-verify-${c.index}`}
                  aria-label={`Verify source ${c.index} — review above article, then click Verify below`}
                >
                  {busy ? (
                    "Checking…"
                  ) : (
                    <>
                      <span className="cite-nudge-emoji" aria-hidden="true">🤔</span>
                      Review above article, then click
                      <span className="cite-nudge-verify-word"> Verify</span>
                      <span className="cite-nudge-point" aria-hidden="true"> 👆</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
