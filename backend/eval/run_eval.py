import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import Settings  # noqa: E402
from app.graph.builder import build_graph  # noqa: E402
from app.graph.nodes.cite import cite  # noqa: E402
from app.graph.nodes.generate import generate  # noqa: E402
from app.retrieval import faiss_store  # noqa: E402
from app.schemas.eval import EvalItem, EvalRecord, EvalRun  # noqa: E402
from app.schemas.retrieval import ContextSource  # noqa: E402
from eval.answer import answer_correct  # noqa: E402
from eval.grade import apply_manual_overrides, grade_answer, load_overrides  # noqa: E402
from eval.judge_dev import load_items, load_thresholds  # noqa: E402
from eval.report import build_summary, render_markdown  # noqa: E402

EVAL_ROOT = BACKEND_ROOT / "eval" / "results"


def build_record(item: EvalItem, mode: str, payload: dict[str, Any], grade: str, grade_source: str) -> dict[str, Any]:
    report = payload.get("citation_report") or {}
    return {
        "qid": item.qid,
        "category": item.category,
        "mode": mode,
        "expected_branch": item.expected_branch if mode == "crag" else None,
        "actual_branch": payload.get("retrieval_decision"),
        "branch_correct": payload.get("retrieval_decision") == item.expected_branch if mode == "crag" else None,
        "answer": payload.get("answer", ""),
        "abstained": payload.get("abstained", False),
        "grade": grade,
        "grade_source": grade_source,
        "answer_correct": answer_correct(grade, payload.get("abstained", False), item.acceptable_abstain),
        "unsupported_claims": payload.get("unsupported_claims", 0),
        "citation_valid": not report.get("invalid_ids", []),
        "citation_coverage": report.get("coverage", 0.0),
        "confidence": payload.get("confidence", 0.0),
        "max_chunk_score": payload.get("max_chunk_score"),
        "sources": [source.get("label", source.get("id", "")) for source in payload.get("sources", [])],
        "latency_ms": payload.get("latency_ms", 0),
        "trace_url": payload.get("trace_url"),
    }


async def run_naive(question: str, settings: Settings) -> dict[str, Any]:
    start = perf_counter()
    results = faiss_store.similarity_search(question, k=settings.naive_k)
    sources = [
        ContextSource(
            sid=f"S{index}",
            kind="corpus",
            ref_id=result["chunk_id"],
            label=result["metadata"].get("citation_label", result["chunk_id"]),
            url=result["metadata"].get("url", ""),
            text=result["display_text"],
            relevance=result["similarity"],
        )
        for index, result in enumerate(results, start=1)
    ]
    state = {"question": question, "context_sources": sources, "retrieval_decision": None, "warnings": []}
    draft = await generate(state, settings)
    cited = await cite({**state, **draft}, settings)
    return {
        **draft,
        **cited,
        "retrieval_decision": None,
        "max_chunk_score": max([result["similarity"] for result in results], default=None),
        "sources": [source.model_dump() for source in cited.get("sources", [])],
        "latency_ms": int((perf_counter() - start) * 1000),
        "trace_url": None,
    }


async def run_crag(question: str, settings: Settings, graph) -> dict[str, Any]:
    start = perf_counter()
    state = await graph.ainvoke(
        {"question": question, "mode": "crag", "warnings": [], "timings_ms": {}},
        config={"run_name": "crag_graph", "tags": ["mode:crag", "split:test"]},
    )
    return {
        **state,
        "sources": [source.model_dump() for source in state.get("sources", [])],
        "max_chunk_score": max(
            [score.score for score in state.get("chunk_scores", []) if score.score is not None],
            default=None,
        ),
        "latency_ms": int((perf_counter() - start) * 1000),
        "trace_url": None,
    }


def load_cache_file(name: str) -> dict[str, Any]:
    path = EVAL_ROOT / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _serializable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: _serializable(item) for key, item in value.items()}
    return value


def save_cache_file(name: str, value: dict[str, Any]) -> None:
    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    content = json.dumps(_serializable(value), ensure_ascii=False, indent=2)
    (EVAL_ROOT / name).write_text(content, encoding="utf-8")


async def try_langsmith_experiment(run: EvalRun, items: list[EvalItem]) -> str | None:
    if not run.config.get("langsmith_tracing"):
        return None
    try:
        from langsmith import Client

        client = Client(api_key=run.config.get("langsmith_api_key"))
        dataset = client.create_dataset(name=f"legal-crag-{run.run_id}", examples=[])
        for item in items:
            client.create_example(
                dataset_id=dataset.id,
                inputs={"question": item.question},
                outputs={"expected_branch": item.expected_branch, "reference_points": item.reference_points},
                metadata={"eval_qid": item.qid, "category": item.category},
            )
        return f"legal-crag-{run.run_id}"
    except Exception:
        return None


async def main() -> None:
    thresholds = load_thresholds()
    settings = Settings(
        judge_concurrency=3,
        upper_threshold=thresholds["upper_threshold"],
        lower_threshold=thresholds["lower_threshold"],
        keep_threshold=thresholds["keep_threshold"],
        langsmith_tracing=False,
    )
    items = load_items(BACKEND_ROOT / "eval" / "datasets" / "test_set.jsonl")
    graph = build_graph(settings)
    answer_cache = load_cache_file("eval_answer_cache.json")
    grade_cache = load_cache_file("eval_grade_cache.json")
    records: list[dict[str, Any]] = []

    for item in items:
        for mode in ("naive", "crag"):
            key = f"{item.qid}:{mode}:{settings.groq_gen_model}:V1"
            if key in answer_cache:
                payload = answer_cache[key]
            else:
                payload = (
                    await run_naive(item.question, settings)
                    if mode == "naive"
                    else await run_crag(item.question, settings, graph)
                )
                answer_cache[key] = payload
                save_cache_file("eval_answer_cache.json", answer_cache)

            grade_key = f"{key}:{payload['answer']}"
            if grade_key in grade_cache:
                grade = grade_cache[grade_key]
            else:
                grade = await grade_answer(
                    item,
                    payload["answer"],
                    payload.get("sources", []),
                    payload.get("abstained", False),
                    settings,
                )
                grade_cache[grade_key] = grade
                save_cache_file("eval_grade_cache.json", grade_cache)

            record = build_record(
                item,
                mode,
                {**payload, "unsupported_claims": grade["unsupported_claims"]},
                grade["grade"],
                grade["grade_source"],
            )
            records.append(record)

    records = apply_manual_overrides(records, load_overrides(), items)
    now = datetime.now(timezone.utc)
    run = EvalRun(
        run_id=now.strftime("%Y-%m-%dT%H-%MZ_crag-v1"),
        created_at=now.isoformat(timespec="seconds"),
        split="test",
        config={
            "models": {
                "judge": settings.groq_judge_model,
                "generator": settings.groq_gen_model,
                "embed": settings.embed_model,
                "rerank": settings.rerank_model,
            },
            "thresholds": {
                "upper": settings.upper_threshold,
                "lower": settings.lower_threshold,
                "keep": settings.keep_threshold,
            },
            "prompt_versions": {"evaluator": settings.evaluator_prompt_version, "generate": "V1", "grader": "V1"},
            "frozen_test_set_sha256": hashlib.sha256(
                (BACKEND_ROOT / "eval" / "datasets" / "test_set.jsonl").read_bytes()
            ).hexdigest(),
            "langsmith_tracing": settings.langsmith_tracing,
        },
        langsmith_experiment=None,
        summary=build_summary(records),
        records=[EvalRecord.model_validate(record) for record in records],
    )
    run.langsmith_experiment = await try_langsmith_experiment(run, items)

    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    (EVAL_ROOT / "results.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
    (EVAL_ROOT / "results.md").write_text(render_markdown(run.model_dump()), encoding="utf-8")
    print(f"Wrote {EVAL_ROOT / 'results.json'} and {EVAL_ROOT / 'results.md'}")


if __name__ == "__main__":
    asyncio.run(main())
