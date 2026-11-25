from typing import Literal

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    chunk_id: str
    citation_label: str
    url: str = ""
    display_text: str
    source_id: str = ""
    doc_type: str = ""
    similarity: float = Field(..., ge=-1, le=1)


class ChunkScore(BaseModel):
    chunk_id: str
    score: float | None = Field(None, ge=0, le=1)
    verdict: Literal["relevant", "partial", "irrelevant"] | None = None
    reason: str | None = None
    jurisdiction_match: bool | None = None
    kept: bool = False
    error: bool = False


class WebResult(BaseModel):
    result_id: str
    url: str
    domain: str
    title: str
    content: str
    tavily_score: float | None = None
    rerank_score: float = 0.0
    domain_trust: float = 0.3
    final_score: float = 0.0
    retrieved_at: str = ""


class ContextSource(BaseModel):
    sid: str
    kind: Literal["corpus", "web"]
    ref_id: str
    label: str
    title: str | None = None
    url: str
    text: str
    relevance: float


def render_sources(sources: list[ContextSource]) -> str:
    return "\n\n".join(f"[{source.sid}] ({source.kind}) {source.label}\n{source.text}" for source in sources)
