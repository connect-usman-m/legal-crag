from typing import Any
from uuid import uuid4

from langsmith import traceable

from app.core.config import Settings


def new_trace_id() -> str:
    return str(uuid4())


def _score_field(score, name: str):
    return getattr(score, name, score.get(name) if isinstance(score, dict) else None)


def apply_trace_metadata(run_tree, payload: dict[str, Any], result: dict[str, Any], **thresholds: float) -> None:
    chunk_scores = [_score_field(score, "score") for score in result.get("chunk_scores", [])]
    kept_chunks = sum(bool(_score_field(score, "kept")) for score in result.get("chunk_scores", []))
    run_tree.add_metadata(
        {
            "request_id": payload["request_id"],
            "mode": payload["mode"],
            "retrieval_decision": result.get("retrieval_decision"),
            "max_chunk_score": max([score for score in chunk_scores if score is not None], default=None),
            "kept_chunks": kept_chunks,
            "web_results_used": len(result.get("web_results", [])),
            "abstained": result.get("abstained", False),
            "confidence": result.get("confidence", 0.0),
            "citation_coverage": result.get("citation_report", {}).get("coverage", 0.0),
            "warnings": result.get("warnings", []),
            "thresholds": thresholds,
            "prompt_versions": {"evaluator": "V3", "generate": "V1"},
            "corpus_version": "gdpr_v1",
        }
    )
    if result.get("retrieval_decision"):
        run_tree.add_tags([f"mode:{payload['mode']}", f"decision:{result['retrieval_decision']}"])


@traceable(name="crag_query")
async def traced_query(
    payload: dict[str, Any],
    runner,
    settings: Settings,
    run_tree=None,
) -> dict[str, Any]:
    result = await runner()
    trace_id = str(run_tree.id) if run_tree is not None else new_trace_id()
    trace_url = None
    if run_tree is not None:
        try:
            trace_url = run_tree.get_url()
        except Exception:
            trace_url = None
        apply_trace_metadata(
            run_tree,
            payload,
            result,
            upper=settings.upper_threshold,
            lower=settings.lower_threshold,
            keep=settings.keep_threshold,
        )
    return {**result, "trace_id": trace_id, "trace_url": trace_url}
