export type VerificationStatus = "verified" | "unverified";

export interface Citation {
  index: number;
  chunk_id: string;
  document_title: string;
  verification_status: VerificationStatus;
  source_url?: string | null;
  publication_date?: string | null;
}

export interface QuerySuggestion {
  label: string;
  query: string;
  chunk_id: string;
  source_org: string;
  document_id?: string | null;
}

export interface StarterPrompt {
  id: string;
  label: string;
  query: string;
  kind: "corpus" | "off_topic";
  chunk_id?: string;
  source_org?: string;
  document_id?: string | null;
}

export interface QueryResponse {
  session_id: string;
  answer: string;
  citations: Citation[];
  model_used: string;
  refused: boolean;
  retrieval_ms: number | null;
  out_of_corpus: boolean;
  needs_clarification?: boolean;
  retrieval_mode?: string | null;
  groq_live?: boolean | null;
  suggested_queries: QuerySuggestion[];
  indexed_count?: number | null;
  live_source_count?: number | null;
  coverage_note?: string | null;
}

export interface ChunkDetail {
  chunk_id: string;
  source_url: string;
  document_title: string;
  publication_year: number;
  page_number: number;
  exact_context: string;
  verification_status: VerificationStatus;
  source_org: string;
  content_hash: string | null;
}

export interface ExportGate {
  allowed: boolean;
  total: number;
  verified: number;
  pending_indices: number[];
}

export interface HealthResponse {
  status: string;
  chroma: string;
  rag_retrieval?: string | null;
  groq_live?: boolean | null;
  embed_mock?: boolean | null;
}
