const STORAGE_KEY = "hitl_clarification_session";

export interface ClarificationContext {
  sessionId: string;
  anchorQuery: string;
}

export function loadClarificationContext(): ClarificationContext | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ClarificationContext;
    if (parsed.sessionId && parsed.anchorQuery) return parsed;
  } catch {
    /* ignore */
  }
  return null;
}

export function saveClarificationContext(ctx: ClarificationContext): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(ctx));
}

export function clearClarificationContext(): void {
  localStorage.removeItem(STORAGE_KEY);
}

/** True when the follow-up query likely narrows the prior clarification ask. */
export function isClarificationFollowUp(currentQuery: string, anchorQuery: string): boolean {
  const tokenize = (text: string) =>
    new Set(
      (text.toLowerCase().match(/\b[a-z0-9]{4,}\b/g) ?? []).filter(
        (w) => !["what", "when", "where", "which", "about", "want", "main"].includes(w)
      )
    );
  const current = tokenize(currentQuery);
  const anchor = tokenize(anchorQuery);
  if (current.size === 0 || anchor.size === 0) return false;
  let overlap = 0;
  for (const w of current) {
    if (anchor.has(w)) overlap += 1;
  }
  if (overlap >= 2) return true;
  const anchorSnippet = anchorQuery.trim().toLowerCase().slice(0, 48);
  return (
    anchorSnippet.length > 12 &&
    currentQuery.trim().toLowerCase().includes(anchorSnippet)
  );
}
