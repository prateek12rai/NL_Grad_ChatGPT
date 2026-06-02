import type { ChunkDetail, Citation } from "../api/types";
import { buildTextFragment } from "../lib/textFragment";

interface SourcePreviewPanelProps {
  citation: Citation | null;
  chunk: ChunkDetail | null;
  loading: boolean;
  error: string | null;
  anchorQuery: string;
}

export function SourcePreviewPanel({
  citation,
  chunk,
  loading,
  error,
  anchorQuery,
}: SourcePreviewPanelProps) {
  if (!citation) return null;

  const openArticleAtExcerpt = () => {
    if (!citation.source_url) return;
    const raw = (chunk?.exact_context ?? "").trim();
    const { fragment } = buildTextFragment(raw, anchorQuery);
    window.open(`${citation.source_url}${fragment}`, "_blank", "noopener,noreferrer");
  };

  return (
    <aside
      className="source-preview"
      data-testid="source-preview-panel"
      aria-label={`Source preview for citation ${citation.index}`}
    >
      <h3 className="source-preview-title">
        Source [{citation.index}] — <strong>Review</strong> before you verify
      </h3>
      <dl className="source-preview-meta">
        <div>
          <dt>Document</dt>
          <dd>{citation.document_title}</dd>
        </div>
        {citation.publication_date && (
          <div>
            <dt>Published</dt>
            <dd>{citation.publication_date}</dd>
          </div>
        )}
        {citation.source_url && (
          <div>
            <dt>URL</dt>
            <dd>
              <button
                type="button"
                className="btn-open-article"
                onClick={openArticleAtExcerpt}
                aria-label="Open the full article on Nature"
              >
                Open article on Nature
              </button>
            </dd>
          </div>
        )}
      </dl>

      {loading && (
        <p className="loading" data-testid="source-preview-loading">
          Loading excerpt from indexed corpus…
        </p>
      )}
      {error && (
        <p className="error" role="alert" data-testid="source-preview-error">
          {error}
        </p>
      )}
    </aside>
  );
}
