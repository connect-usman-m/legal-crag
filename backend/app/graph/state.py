import operator
from typing import Annotated, Literal, TypedDict

from app.schemas.retrieval import ChunkScore, ContextSource, RetrievedChunk, WebResult

Decision = Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]


class CitationReport(TypedDict):
    valid_ids: list[str]
    invalid_ids: list[str]
    unused_ids: list[str]
    factual_sentences: int
    cited_sentences: int
    coverage: float


def merge_timings(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return {**left, **right}


def chunk_field(chunk: object, name: str, default: object = None) -> object:
    if hasattr(chunk, name):
        return getattr(chunk, name)
    return chunk.get(name, default) if isinstance(chunk, dict) else default


class CRAGState(TypedDict, total=False):
    request_id: str
    question: str
    mode: Literal["crag", "naive"]

    retrieved: list[RetrievedChunk]
    chunk_scores: list[ChunkScore]
    retrieval_decision: Decision
    decision_reason: str

    web_query: str | None
    web_results: list[WebResult]
    context_sources: list[ContextSource]

    draft_answer: str
    used_source_ids: list[str]
    abstained: bool
    generation_attempts: int

    answer: str
    sources: list[ContextSource]
    citation_report: CitationReport
    confidence: float
    confidence_label: Literal["High", "Medium", "Low", "None"]

    warnings: Annotated[list[str], operator.add]
    timings_ms: Annotated[dict[str, int], merge_timings]
