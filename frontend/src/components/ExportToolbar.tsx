import { useState } from "react";
import type { ExportGate } from "../api/types";
import { ShareBar } from "./ShareBar";

interface ExportToolbarProps {
  gate: ExportGate | null;
  answer: string;
}

export function ExportToolbar({ gate, answer }: ExportToolbarProps) {
  const allowed = gate?.allowed === true;
  const pending = gate?.pending_indices ?? [];
  const [shareOpen, setShareOpen] = useState(false);
  const tooltip =
    allowed
      ? "All cited sources are verified. You may copy or share."
      : pending.length > 0
        ? `Locked: verify reference(s) ${pending.map((i) => `[${i}]`).join(", ")} first.`
        : "Verify every cited source before copy or share.";

  const handleCopy = async () => {
    if (!allowed || !answer) return;
    await navigator.clipboard.writeText(answer);
  };

  return (
    <footer className="export-toolbar" data-testid="export-toolbar">
      <div className="export-status" title={tooltip}>
        {allowed ? (
          <span className="gate-open" data-testid="export-gate-open">
            Share &amp; copy unlocked ({gate?.verified}/{gate?.total} cited sources verified)
          </span>
        ) : (
          <span className="gate-locked" data-testid="export-gate-locked">
            Share / Copy locked — verify all cited sources first
          </span>
        )}
      </div>
      <div className="export-actions">
        <div className="share-action-wrap">
          <button
            type="button"
            className="btn-export"
            onClick={() => setShareOpen((v) => !v)}
            disabled={!allowed}
            aria-label="Share verified answer"
            aria-expanded={shareOpen}
            title={tooltip}
            data-testid="btn-share"
          >
            Share
          </button>
          <ShareBar open={shareOpen && allowed} onClose={() => setShareOpen(false)} />
        </div>
        <button
          type="button"
          className="btn-export"
          onClick={() => void handleCopy()}
          disabled={!allowed}
          aria-label="Copy verified answer to clipboard"
          title={tooltip}
          data-testid="btn-copy"
        >
          Copy answer
        </button>
      </div>
    </footer>
  );
}
