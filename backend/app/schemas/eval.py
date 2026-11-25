from typing import Literal

from pydantic import BaseModel, Field


class EvalItem(BaseModel):
    qid: str
    split: Literal["dev", "test"]
    category: Literal["covered", "not_covered", "ambiguous"]
    question: str
    expected_branch: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]
    reference_points: list[str] = Field(default_factory=list)
    expected_corpus_refs: list[str] = Field(default_factory=list)
    acceptable_abstain: bool = False
    notes: str | None = None


class EvalRecord(BaseModel):
    qid: str
    category: str
    mode: Literal["naive", "crag"]
    expected_branch: str | None
    actual_branch: str | None
    branch_correct: bool | None
    answer: str
    abstained: bool
    grade: Literal["correct", "partial", "incorrect", "abstained"]
    grade_source: Literal["llm", "manual"]
    answer_correct: bool
    unsupported_claims: int
    citation_valid: bool
    citation_coverage: float
    confidence: float
    max_chunk_score: float | None
    sources: list[str]
    latency_ms: int
    trace_url: str | None


class EvalSummary(BaseModel):
    branch_accuracy: float
    answer_accuracy: dict[str, float]
    by_category: dict[str, dict[str, int]]
    hallucinations: dict[str, int]
    citation_validity: dict[str, float]
    p50_latency_ms: dict[str, int]


class EvalRun(BaseModel):
    run_id: str
    created_at: str
    split: Literal["dev", "test"]
    config: dict
    langsmith_experiment: str | None
    summary: EvalSummary
    records: list[EvalRecord]
