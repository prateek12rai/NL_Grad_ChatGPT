import type { StarterPrompt } from "../api/types";
import { GlassSearchBar } from "./GlassSearchBar";

function CorpusLockIcon() {
  return (
    <span className="starter-icon starter-icon--medical" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="18" height="18">
        <path
          fill="currentColor"
          d="M12 2a5 5 0 0 1 5 5v2h1a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V11a2 2 0 0 1 2-2h1V7a5 5 0 0 1 5-5Zm0 2a3 3 0 0 0-3 3v2h6V7a3 3 0 0 0-3-3Z"
        />
      </svg>
    </span>
  );
}

interface GlassLandingProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: () => void;
  loading: boolean;
  starters: StarterPrompt[];
  onStarterClick: (prompt: StarterPrompt) => void;
}

export function GlassLanding({
  query,
  onQueryChange,
  onSubmit,
  loading,
  starters,
  onStarterClick,
}: GlassLandingProps) {
  return (
    <section className="glass-landing" data-testid="glass-landing">
      <div className="glass-hero" data-testid="glass-hero">
        <h1 className="glass-title">ChatGPT Glass</h1>
        <p className="glass-tagline">(We deliver Real facts only)</p>
      </div>

      <GlassSearchBar
        value={query}
        onChange={onQueryChange}
        onSubmit={onSubmit}
        loading={loading}
      />

      <ul className="starter-list" data-testid="starter-prompts">
        {starters.map((item, index) => (
          <li key={item.id}>
            <button
              type="button"
              className={`starter-prompt starter-prompt--${item.kind}`}
              data-testid={`starter-prompt-${index}`}
              onClick={() => onStarterClick(item)}
              disabled={loading}
            >
              {item.kind === "corpus" ? <CorpusLockIcon /> : null}
              <span className="starter-prompt-label">{item.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
