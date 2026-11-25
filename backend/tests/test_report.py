from eval.report import build_summary, render_markdown


def _record(qid, mode, category, grade, branch=None, latency=100):
    correct = grade in {"correct"} or (grade == "abstained" and qid == "T15")
    expected = {
        "covered": "CORRECT",
        "not_covered": "INCORRECT",
        "ambiguous": "AMBIGUOUS",
    }[category]
    return {
        "qid": qid,
        "mode": mode,
        "category": category,
        "expected_branch": expected,
        "actual_branch": branch,
        "branch_correct": branch == expected if mode == "crag" else None,
        "grade": grade,
        "answer_correct": correct,
        "citation_valid": True,
        "citation_coverage": 1.0,
        "unsupported_claims": 0,
        "latency_ms": latency,
    }


def test_build_summary_counts_by_category_and_mode():
    records = [
        _record("T01", "naive", "covered", "correct"),
        _record("T01", "crag", "covered", "correct", "CORRECT"),
        _record("T06", "naive", "not_covered", "incorrect"),
        _record("T06", "crag", "not_covered", "correct", "INCORRECT"),
        _record("T15", "crag", "ambiguous", "abstained", "AMBIGUOUS"),
    ]

    summary = build_summary(records)

    assert summary["answer_accuracy"]["naive"] == 0.5
    assert summary["answer_accuracy"]["crag"] == 1.0
    assert summary["by_category"]["covered"]["naive"] == 1
    assert summary["branch_accuracy"] == 1.0
    assert summary["citation_validity"]["crag"] == 1.0


def test_render_markdown_has_table_and_category_summary():
    records = [
        _record("T01", "naive", "covered", "correct"),
        _record("T01", "crag", "covered", "correct", "CORRECT"),
    ]
    summary = build_summary(records)
    run = {"run_id": "test-run", "summary": summary, "records": records, "config": {"prompt_version": "V1"}}

    text = render_markdown(run)

    assert "| T01 |" in text
    assert "| Covered |" in text
    assert "test-run" in text
