function tokens(text: string): string[] {
  return (text.toLowerCase().match(/\b[a-z0-9]{4,}\b/g) ?? []).filter(
    (t) =>
      ![
        "what",
        "when",
        "where",
        "which",
        "about",
        "does",
        "have",
        "been",
        "were",
        "with",
        "from",
        "that",
        "this",
        "your",
        "their",
        "would",
        "could",
        "should",
        "study",
        "paper",
        "article",
        "nature",
      ].includes(t)
  );
}

function splitSentences(text: string): string[] {
  const normalized = (text || "").replace(/\s+/g, " ").trim();
  if (!normalized) return [];
  // Best-effort sentence split; OK for prose chunks.
  const parts = normalized.split(/(?<=[.!?])\s+/);
  return parts.map((p) => p.trim()).filter(Boolean);
}

export function bestTextFragmentSnippet(
  excerpt: string,
  anchorQuery: string,
  options?: { maxLen?: number }
): string {
  const maxLen = options?.maxLen ?? 160;
  const ex = (excerpt || "").replace(/\s+/g, " ").trim();
  if (!ex) return "";

  const qTokens = new Set(tokens(anchorQuery));
  const sentences = splitSentences(ex);

  if (sentences.length === 0 || qTokens.size === 0) {
    return ex.slice(0, maxLen);
  }

  let best = "";
  let bestScore = -1;

  for (const s of sentences) {
    const sTokens = tokens(s);
    if (sTokens.length === 0) continue;
    const overlap = sTokens.reduce((acc, t) => acc + (qTokens.has(t) ? 1 : 0), 0);

    // Prefer sentences that match the query and are not too short/long.
    const lenPenalty = s.length < 40 ? 1 : s.length > 240 ? 1 : 0;
    const score = overlap * 10 - lenPenalty;

    if (score > bestScore) {
      bestScore = score;
      best = s;
    }
  }

  const chosen = best || ex;
  return chosen.slice(0, maxLen);
}

function phraseFromWords(words: string[], start: number, count: number): string {
  return words.slice(start, start + count).join(" ").trim();
}

export function buildTextFragment(
  excerpt: string,
  anchorQuery: string
): { fragment: string; snippet: string } {
  const snippet = bestTextFragmentSnippet(excerpt, anchorQuery, { maxLen: 220 })
    .replace(/\s+/g, " ")
    .trim();

  const words = snippet.split(" ").filter(Boolean);
  if (words.length < 6) {
    const single = snippet.slice(0, 140);
    return {
      snippet: single,
      fragment: single ? `#:~:text=${encodeURIComponent(single)}` : "",
    };
  }

  // Use short start/end phrases to match despite HTML normalization.
  const start = phraseFromWords(words, 0, 6);
  const end = phraseFromWords(words, Math.max(0, words.length - 6), 6);
  const frag = `#:~:text=${encodeURIComponent(start)},${encodeURIComponent(end)}`;
  return { fragment: frag, snippet };
}

