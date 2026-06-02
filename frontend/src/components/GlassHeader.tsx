interface GlassHeaderProps {
  health: string;
  onNewChat?: () => void;
  showNewChat?: boolean;
}

export function GlassHeader({ health, onNewChat, showNewChat }: GlassHeaderProps) {
  return (
    <header className="glass-header" data-testid="glass-header">
      <div className="glass-header-brand">
        <span className="glass-header-logo">ChatGPT Glass</span>
        {showNewChat && onNewChat && (
          <button
            type="button"
            className="glass-btn-new-chat"
            onClick={onNewChat}
            data-testid="btn-new-chat"
          >
            New chat
          </button>
        )}
      </div>
      <p className="glass-header-health" data-testid="backend-health" title={health}>
        {health}
      </p>
    </header>
  );
}
