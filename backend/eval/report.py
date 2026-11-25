import json
from pathlib import Path
from statistics import median

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def build_summary(records: list[dict]) -> dict:
    modes = ("naive", "crag")
    summary = {
        "branch_accuracy": 0.0,
        "answer_accuracy": {},
        "by_category": {category: {mode: 0 for mode in modes} for category in ("covered", "not_covered", "ambiguous")},
        "hallucinations": {mode: 0 for mode in modes},
        "citation_validity": {},
        "p50_latency_ms": {},
    }
    for mode in modes:
        mode_records = [record for record in records if record["mode"] == mode]
        if mode_records:
            summary["answer_accuracy"][mode] = round(
                sum(record["answer_correct"] for record in mode_records) / len(mode_records), 4
            )
            summary["citation_validity"][mode] = round(
                sum(record["citation_valid"] for record in mode_records) / len(mode_records), 4
            )
            summary["p50_latency_ms"][mode] = int(median(record["latency_ms"] for record in mode_records))
        summary["hallucinations"][mode] = sum(record["unsupported_claims"] > 0 for record in mode_records)
        for record in mode_records:
            if record["answer_correct"]:
                summary["by_category"][record["category"]][mode] += 1
    crag_records = [record for record in records if record["mode"] == "crag"]
    checked = [record for record in crag_records if record["branch_correct"] is not None]
    if checked:
        summary["branch_accuracy"] = round(sum(record["branch_correct"] for record in checked) / len(checked), 4)
    return summary


def _mark(value: bool | None) -> str:
    if value is None:
        return "-"
    return "✓" if value else "✗"


def render_markdown(run: dict) -> str:
    summary = run["summary"]
    lines = [
        "# Evaluation results",
        "",
        f"Run: `{run['run_id']}` — split: `{run.get('split', 'test')}`",
        "",
        "## Per-question results",
        "",
        "| # | Category | Naive | CRAG | CRAG branch | Naive trace | CRAG trace |",
        "|---|---|---|---|---|---|---|",
    ]
    naive_by_qid = {record["qid"]: record for record in run["records"] if record["mode"] == "naive"}
    for record in [record for record in run["records"] if record["mode"] == "crag"]:
        naive = naive_by_qid.get(record["qid"], {})
        naive_link = f"[trace]({naive['trace_url']})" if naive.get("trace_url") else "-"
        crag_link = f"[trace]({record['trace_url']})" if record.get("trace_url") else "-"
        lines.append(
            f"| {record['qid']} | {record['category']} | {_mark(naive.get('answer_correct'))} "
            f"| {_mark(record['answer_correct'])} | {_mark(record['branch_correct'])} "
            f"| {naive_link} | {crag_link} |"
        )
    lines.extend(
        [
            "",
            "## By category",
            "",
            "| Category | Naive correct | CRAG correct |",
            "|---|---:|---:|",
        ]
    )
    labels = {"covered": "Covered", "not_covered": "Not covered", "ambiguous": "Ambiguous"}
    totals = {
        category: sum(record["mode"] == "crag" for record in run["records"] if record["category"] == category)
        for category in summary["by_category"]
    }
    for category, counts in summary["by_category"].items():
        total = totals[category]
        lines.append(f"| {labels[category]} | {counts['naive']}/{total} | {counts['crag']}/{total} |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Branch accuracy (CRAG): {summary['branch_accuracy']:.0%}",
            f"- Answer accuracy: naive {summary['answer_accuracy'].get('naive', 0):.0%}, "
            f"CRAG {summary['answer_accuracy'].get('crag', 0):.0%}",
            f"- Citation validity: naive {summary['citation_validity'].get('naive', 0):.0%}, "
            f"CRAG {summary['citation_validity'].get('crag', 0):.0%}",
            f"- p50 latency (ms): naive {summary['p50_latency_ms'].get('naive', 0)}, "
            f"CRAG {summary['p50_latency_ms'].get('crag', 0)}",
            "",
            "Trace links are shown when LangSmith tracing is enabled and the API key is valid.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    results_path = BACKEND_ROOT / "eval" / "results" / "results.json"
    run = json.loads(results_path.read_text(encoding="utf-8"))
    output = BACKEND_ROOT / "eval" / "results" / "results.md"
    output.write_text(render_markdown(run), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
