import type { StarterPrompt } from "../api/types";
import { GlassSearchBar } from "./GlassSearchBar";

function PremiumAppMark() {
  return (
    <div className="glass-premium-mark">
      <span className="glass-premium-mark-dot" aria-hidden="true" />
      <span className="glass-premium-mark-name">ChatGPT Glass</span>
    </div>
  );
}

function CardIcon({ kind }: { kind: StarterPrompt["kind"] }) {
  const label = kind === "corpus" ? "Medical" : "Demo";
  return (
    <span
      className={`glass-premium-card-icon glass-premium-card-icon--${kind}`}
      aria-label={label}
      title={label}
    >
      {kind === "corpus" ? (
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path
            fill="currentColor"
            d="M12 2a5 5 0 0 1 5 5v2h1a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V11a2 2 0 0 1 2-2h1V7a5 5 0 0 1 5-5Zm0 2a3 3 0 0 0-3 3v2h6V7a3 3 0 0 0-3-3Z"
          />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path
            fill="currentColor"
            d="M12 2a10 10 0 1 0 .001 20.001A10 10 0 0 0 12 2Zm1 15h-2v-2h2v2Zm0-4h-2V7h2v6Z"
          />
        </svg>
      )}
    </span>
  );
}

interface GlassLandingPremiumProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: () => void;
  loading: boolean;
  starters: StarterPrompt[];
  onStarterClick: (prompt: StarterPrompt) => void;
}

export function GlassLandingPremium({
  query,
  onQueryChange,
  onSubmit,
  loading,
  starters,
  onStarterClick,
}: GlassLandingPremiumProps) {
  return (
    <section className="glass-premium" data-testid="glass-landing-premium">
      <div className="glass-premium-bg" aria-hidden="true" />

      <header className="glass-premium-top">
        <PremiumAppMark />
      </header>

      <div className="glass-premium-content">
        <div className="glass-premium-hero">
          <h1 className="glass-premium-title">What&apos;s on your mind today?</h1>
          <p className="glass-premium-tagline">(We deliver Real facts only)</p>
        </div>

        <ul className="glass-premium-cards" data-testid="starter-prompts">
          {starters.map((item, index) => (
            <li key={item.id} className="glass-premium-card-li">
              <button
                type="button"
                className="glass-premium-card"
                data-testid={`starter-prompt-${index}`}
                onClick={() => onStarterClick(item)}
                disabled={loading}
              >
                <CardIcon kind={item.kind} />
                <span className="glass-premium-card-text">
                  <span className="glass-premium-card-title">{item.label}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <footer className="glass-premium-input">
        <div className="glass-premium-input-inner">
          <GlassSearchBar
            value={query}
            onChange={onQueryChange}
            onSubmit={onSubmit}
            loading={loading}
            placeholder="Message ChatGPT Glass…"
          />
        </div>
      </footer>
    </section>
  );
}

