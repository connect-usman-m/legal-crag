from typing import Any

from app.graph.decision import select_kept
from app.graph.state import chunk_field
from app.schemas.retrieval import ContextSource


def passthrough(state: dict[str, Any], keep: float = 0.5) -> dict[str, Any]:
    scores = select_kept(state.get("chunk_scores", []), keep)
    by_id = {score.chunk_id: score for score in scores}
    sources: list[ContextSource] = []
    for chunk in state.get("retrieved", []):
        chunk_id = str(chunk_field(chunk, "chunk_id"))
        if chunk_id not in by_id or not by_id[chunk_id].kept:
            continue
        sources.append(
            ContextSource(
                sid=f"S{len(sources) + 1}",
                kind="corpus",
                ref_id=chunk_id,
                label=str(chunk_field(chunk, "citation_label", chunk_id)),
                url=str(chunk_field(chunk, "url", "")),
                text=str(chunk_field(chunk, "display_text", "")),
                relevance=float(by_id[chunk_id].score or 0),
            )
        )
    return {"chunk_scores": scores, "context_sources": sources}
