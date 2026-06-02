interface GlassSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  placeholder?: string;
  compact?: boolean;
}

export function GlassSearchBar({
  value,
  onChange,
  onSubmit,
  loading = false,
  placeholder = "Ask anything",
  compact = false,
}: GlassSearchBarProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading && value.trim()) onSubmit();
    }
  };

  return (
    <div
      className={`glass-search ${compact ? "glass-search--compact" : "glass-search--centered"}`}
      data-testid="glass-search"
    >
      <div className="glass-search-inner">
        <span className="glass-search-plus" aria-hidden="true">
          +
        </span>
        <textarea
          className="glass-search-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={loading}
          data-testid="query-input"
          aria-label="Ask a question"
          rows={compact ? 2 : 3}
        />
        <button
          type="button"
          className="glass-search-submit"
          onClick={onSubmit}
          disabled={loading || !value.trim()}
          data-testid="btn-submit-query"
          aria-busy={loading}
          aria-label={loading ? "Working on answer" : "Submit question"}
        >
          {loading ? (
            <span className="glass-search-spinner" aria-hidden="true" />
          ) : (
            <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
              <path
                fill="currentColor"
                d="M3.4 20.4 20.4 3.4a1.5 1.5 0 0 1 2.1 2.1L5.5 22.5a1.5 1.5 0 0 1-2.1-2.1Zm16.2-14.3-2.1 2.1-2.1-2.1 2.1-2.1 2.1 2.1Z"
              />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
