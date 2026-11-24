import json
import sys
from collections import Counter
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from eval.judge_dev import load_thresholds  # noqa: E402

LABELS = ("relevant", "partial", "irrelevant")
BUCKETS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def histogram(rows: list[dict]) -> dict[str, Counter]:
    result = {label: Counter() for label in LABELS}
    for row in rows:
        score = row["score"]
        if row["label"] not in result or score is None:
            continue
        bucket = min(int(score * 5), 4)
        label = f"{BUCKETS[bucket]:.1f}-{BUCKETS[bucket + 1]:.1f}"
        result[row["label"]][label] += 1
    return result


def main() -> None:
    data = json.loads((BACKEND_ROOT / "eval" / "results" / "judge_dev.json").read_text(encoding="utf-8"))
    rows = data["rows"]
    thresholds = load_thresholds()
    counts = histogram(rows)
    lines = [
        "# Calibration",
        "",
        "Dev set only. The frozen test set was not used for tuning.",
        "",
        f"Prompt version: {thresholds['prompt_version']}",
        "Thresholds: "
        f"LOWER={thresholds['lower_threshold']}, "
        f"KEEP={thresholds['keep_threshold']}, "
        f"UPPER={thresholds['upper_threshold']}",
        "",
        "## Score histogram",
        "",
    ]
    for label in LABELS:
        lines.append(f"### {label}")
        lines.append("")
        for bucket in (f"{BUCKETS[i]:.1f}-{BUCKETS[i + 1]:.1f}" for i in range(5)):
            count = counts[label][bucket]
            lines.append(f"- {bucket}: {'#' * count} ({count})")
        lines.append("")
    runs = data["runs"]
    accuracy = sum(run["retrieval_decision"] == run["expected_branch"] for run in runs)
    irrelevant = [row for row in rows if row["label"] == "irrelevant" and row["score"] is not None]
    below = sum(row["score"] < thresholds["lower_threshold"] for row in irrelevant)
    lines.extend(
        [
            "## Outcome",
            "",
            f"- Branch accuracy: {accuracy}/{len(runs)}",
            f"- Irrelevant chunks below LOWER: {below}/{len(irrelevant)}",
            "- V1 reached 6/10; V2 failed with Groq tool-use errors; V3 with strict JSON schema was selected.",
            "- UPPER 0.9 keeps partial cross-instrument chunks out of CORRECT; "
            "LOWER 0.5 captures the remaining high-scoring irrelevant chunks.",
        ]
    )
    (BACKEND_ROOT / "eval" / "results" / "calibration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote calibration.md: {accuracy}/{len(runs)} accuracy, {below}/{len(irrelevant)} irrelevant below LOWER")


if __name__ == "__main__":
    main()
