import type { ExportGate } from "../api/types";

interface VerificationBarProps {
  gate: ExportGate | null;
}

export function VerificationBar({ gate }: VerificationBarProps) {
  if (!gate) return null;

  const pending = gate.pending_indices ?? [];
  const allowed = gate.allowed === true;

  return (
    <div
      className={`verification-bar ${allowed ? "verification-bar--open" : "verification-bar--locked"}`}
      data-testid="verification-bar"
      role="status"
    >
      {allowed ? (
        <p data-testid="verification-bar-open">
          <strong>Sources verified.</strong> You confirmed every citation used in this answer.
          Share and export are unlocked below.
        </p>
      ) : (
        <p data-testid="verification-bar-locked">
          <strong>Human verification required.</strong> Open the article, review it, then click{" "}
          <span className="verification-hint">Verify</span> on the citation
          {pending.length > 0 ? (
            <> (pending: {pending.map((i) => `[${i}]`).join(", ")})</>
          ) : null}{" "}
          to unlock Share / Export.
        </p>
      )}
    </div>
  );
}
