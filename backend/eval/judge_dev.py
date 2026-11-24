import asyncio
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import Settings  # noqa: E402
from app.graph.nodes.evaluate import evaluate_chunks  # noqa: E402
from app.retrieval import chroma_store  # noqa: E402
from app.schemas.eval import EvalItem  # noqa: E402


def load_items(path: Path) -> list[EvalItem]:
    return [EvalItem.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_thresholds() -> dict:
    path = BACKEND_ROOT / "eval" / "results" / "calibration_thresholds.json"
    return json.loads(path.read_text(encoding="utf-8"))


def calibration_rows(runs: list[dict], labels: dict[tuple[str, str], str]) -> list[dict]:
    rows = []
    for run in runs:
        for score in run["chunk_scores"]:
            rows.append(
                {
                    "qid": run["qid"],
                    "chunk_id": score["chunk_id"],
                    "score": score["score"],
                    "verdict": score["verdict"],
                    "label": labels.get((run["qid"], score["chunk_id"]), "unknown"),
                }
            )
    return rows


def hand_labels(items: list[EvalItem]) -> dict[tuple[str, str], str]:
    path = BACKEND_ROOT / "eval" / "results" / "hand_labels.json"
    stored = json.loads(path.read_text(encoding="utf-8"))
    labels = {(qid, chunk_id): label for qid, chunk_map in stored.items() for chunk_id, label in chunk_map.items()}
    for item in items:
        results = chroma_store.similarity_search(item.question, k=6)
        for result in results:
            if (item.qid, result["chunk_id"]) not in labels:
                raise ValueError(f"Missing hand label for {item.qid}:{result['chunk_id']}")
    return labels


async def run_judge_dev() -> None:
    calibrated = load_thresholds()
    settings = Settings(
        judge_concurrency=3,
        evaluator_prompt_version=calibrated["prompt_version"],
        lower_threshold=calibrated["lower_threshold"],
        keep_threshold=calibrated["keep_threshold"],
        upper_threshold=calibrated["upper_threshold"],
    )
    items = load_items(BACKEND_ROOT / "eval" / "datasets" / "dev_set.jsonl")
    labels = hand_labels(items)
    runs = []
    for item in items:
        retrieved = chroma_store.similarity_search(item.question, k=6)
        result = await evaluate_chunks(
            {"question": item.question, "retrieved": retrieved},
            settings,
        )
        runs.append(
            {
                "qid": item.qid,
                "category": item.category,
                "expected_branch": item.expected_branch,
                "question": item.question,
                "retrieved": [{key: value for key, value in chunk.items() if key != "metadata"} for chunk in retrieved],
                **{
                    key: [score.model_dump() for score in result[key]] if key == "chunk_scores" else result[key]
                    for key in ("chunk_scores", "retrieval_decision", "decision_reason")
                },
            }
        )
    rows = calibration_rows(runs, labels)
    output_dir = BACKEND_ROOT / "eval" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "judge_dev.json").write_text(
        json.dumps({"runs": runs, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "judge_dev.csv").write_text(
        "qid,chunk_id,label,score,verdict\n"
        + "\n".join(f"{row['qid']},{row['chunk_id']},{row['label']},{row['score']},{row['verdict']}" for row in rows)
        + "\n",
        encoding="utf-8",
    )
    correct = sum(run["retrieval_decision"] == run["expected_branch"] for run in runs)
    irrelevant = [row for row in rows if row["label"] == "irrelevant" and row["score"] is not None]
    below = sum(row["score"] < settings.lower_threshold for row in irrelevant)
    print(f"branch accuracy {correct}/{len(runs)}; irrelevant below LOWER {below}/{len(irrelevant)}")


def main() -> None:
    asyncio.run(run_judge_dev())


if __name__ == "__main__":
    main()
