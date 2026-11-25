export type Decision = "CORRECT" | "AMBIGUOUS" | "INCORRECT" | null;

export type Mode = "crag" | "naive";

export interface SourceOut {
  id: string;
  type: "corpus" | "web";
  label: string;
  title: string | null;
  url: string;
  snippet: string;
  relevance_score: number;
  used: boolean;
}

export interface ChunkScoreOut {
  chunk_id: string;
  label: string;
  score: number | null;
  verdict: string | null;
  reason: string | null;
  kept: boolean;
}

export interface QueryRequest {
  question: string;
  mode: Mode;
  debug?: boolean;
}

export interface QueryResponse {
  request_id: string;
  mode: Mode;
  question: string;
  answer: string;
  abstained: boolean;
  sources: SourceOut[];
  retrieval_decision: Decision;
  decision_reason: string | null;
  confidence: number;
  confidence_label: "High" | "Medium" | "Low" | "None";
  citation_coverage: number;
  warnings: string[];
  web_query: string | null;
  chunk_scores: ChunkScoreOut[] | null;
  trace_id: string | null;
  trace_url: string | null;
  latency_ms: number;
  timings_ms: Record<string, number> | null;
  models: Record<string, string>;
  prompt_versions: Record<string, string>;
  thresholds: Record<string, number> | null;
}

export interface CompareResponse {
  naive: QueryResponse;
  crag: QueryResponse;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  ready: boolean;
  checks: Record<string, boolean>;
  corpus_version: string | null;
}

export interface EvalRecord {
  qid: string;
  category: string;
  mode: Mode;
  expected_branch: string | null;
  actual_branch: string | null;
  branch_correct: boolean | null;
  answer: string;
  abstained: boolean;
  grade: string;
  grade_source: string;
  answer_correct: boolean;
  unsupported_claims: number;
  citation_valid: boolean;
  citation_coverage: number;
  confidence: number;
  max_chunk_score: number | null;
  sources: string[];
  latency_ms: number;
  trace_url: string | null;
}

export interface EvalSummary {
  branch_accuracy: number;
  answer_accuracy: Record<string, number>;
  by_category: Record<string, Record<string, number>>;
  hallucinations: Record<string, number>;
  citation_validity: Record<string, number>;
  p50_latency_ms: Record<string, number>;
}

export interface EvalRun {
  run_id: string;
  created_at: string;
  split: string;
  config: Record<string, unknown>;
  langsmith_experiment: string | null;
  summary: EvalSummary;
  records: EvalRecord[];
}

export interface ErrorResponse {
  error: string;
  message: string;
  request_id: string;
  retry_after_s: number | null;
}
