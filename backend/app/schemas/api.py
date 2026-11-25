from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    mode: Literal["crag", "naive"] = "crag"
    debug: bool = False


class SourceOut(BaseModel):
    id: str
    type: Literal["corpus", "web"]
    label: str
    title: str | None = None
    url: str
    snippet: str = Field(..., max_length=600)
    relevance_score: float
    used: bool = True


class ChunkScoreOut(BaseModel):
    chunk_id: str
    label: str
    score: float | None
    verdict: str | None
    reason: str | None
    kept: bool


class QueryResponse(BaseModel):
    request_id: str
    mode: Literal["crag", "naive"]
    question: str
    answer: str
    abstained: bool
    sources: list[SourceOut]
    retrieval_decision: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"] | None
    decision_reason: str | None
    confidence: float = Field(..., ge=0, le=1)
    confidence_label: Literal["High", "Medium", "Low", "None"]
    citation_coverage: float
    warnings: list[str]
    web_query: str | None = None
    chunk_scores: list[ChunkScoreOut] | None = None
    trace_id: str | None
    trace_url: str | None
    latency_ms: int
    timings_ms: dict[str, int] | None = None
    models: dict[str, str]
    prompt_versions: dict[str, str]
    thresholds: dict[str, float] | None = None


class CompareRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class CompareResponse(BaseModel):
    naive: QueryResponse
    crag: QueryResponse


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    ready: bool
    checks: dict[str, bool]
    corpus_version: str | None


class CorpusStats(BaseModel):
    corpus_version: str
    built_at: str
    totals: dict[str, int]
    by_source: list[dict]


class ErrorResponse(BaseModel):
    error: Literal[
        "validation_error",
        "unauthorized",
        "rate_limited",
        "upstream_unavailable",
        "index_not_ready",
        "timeout",
        "internal_error",
    ]
    message: str
    request_id: str
    retry_after_s: int | None = None
