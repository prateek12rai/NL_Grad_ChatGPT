import type { StarterPrompt } from "../api/types";

export const FALLBACK_STARTER_PROMPTS: StarterPrompt[] = [
  {
    id: "fallback-1",
    label: "Bedaquiline-resistant TB under revised DOTS",
    query:
      "What does the indexed Nature research say about bedaquiline-resistant tuberculosis and DOTS protocols?",
    kind: "corpus",
    source_org: "Nature",
  },
  {
    id: "fallback-2",
    label: "📅 Show me all research on 29 May 2026",
    query: "Show me all research articles published on 2026-05-29",
    kind: "corpus",
    source_org: "Nature",
  },
  {
    id: "fallback-off-aliens",
    label: "👽 Do you think Aliens have cure for Cancer?",
    query: "Do you think Aliens have cure for Cancer",
    kind: "off_topic",
  },
];
