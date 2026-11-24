from typing import Any

from app.core.config import Settings
from app.graph.decision import select_kept
from app.graph.nodes.web_correct import rewrite_query, search_web, web_sources
from app.graph.state import chunk_field
from app.schemas.retrieval import ContextSource


async def filter_and_supplement(
    state: dict[str, Any],
    settings: Settings | None = None,
    keep: float | None = None,
    web_n: int | None = None,
) -> dict[str, Any]:
    config = settings or Settings()
    kept_scores = select_kept(state.get("chunk_scores", []), keep if keep is not None else config.keep_threshold)
    kept_by_id = {score.chunk_id: score for score in kept_scores if score.kept}
    corpus_sources: list[ContextSource] = []
    for chunk in state.get("retrieved", []):
        chunk_id = str(chunk_field(chunk, "chunk_id"))
        if chunk_id not in kept_by_id:
            continue
        corpus_sources.append(
            ContextSource(
                sid=f"S{len(corpus_sources) + 1}",
                kind="corpus",
                ref_id=chunk_id,
                label=str(chunk_field(chunk, "citation_label", chunk_id)),
                url=str(chunk_field(chunk, "url", "")),
                text=str(chunk_field(chunk, "display_text", "")),
                relevance=float(kept_by_id[chunk_id].score or 0),
            )
        )

    warnings: list[str] = []
    if not corpus_sources:
        warnings.append("no_corpus_chunks_above_keep")

    query = await rewrite_query(state["question"], config)
    try:
        results = search_web(query, config)
        web = results[: web_n or config.web_supplement_n]
    except Exception:
        web = []
        warnings.append("web_search_failed")

    web_as_sources = web_sources(web, len(web))
    for offset, source in enumerate(web_as_sources):
        source.sid = f"S{len(corpus_sources) + offset + 1}"

    return {
        "web_query": query,
        "web_results": web,
        "context_sources": [*corpus_sources, *web_as_sources],
        "chunk_scores": state.get("chunk_scores", []),
        "warnings": warnings,
    }
