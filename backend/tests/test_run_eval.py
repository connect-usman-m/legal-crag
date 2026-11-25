from app.schemas.eval import EvalItem
from app.schemas.retrieval import RetrievedChunk
from eval.run_eval import build_record, save_cache_file


def test_build_record_maps_pipeline_output():
    item = EvalItem(
        qid="T06",
        split="test",
        category="not_covered",
        question="CCPA penalties?",
        expected_branch="INCORRECT",
        reference_points=["Civil penalties"],
    )
    payload = {
        "answer": "CCPA fines [S1].",
        "abstained": False,
        "retrieval_decision": "INCORRECT",
        "decision_reason": "max=0.1",
        "sources": [{"label": "oag.ca.gov"}],
        "confidence": 0.5,
        "citation_report": {"coverage": 1.0, "invalid_ids": []},
        "max_chunk_score": 0.1,
        "latency_ms": 120,
        "trace_url": None,
    }

    record = build_record(item, "crag", payload, grade="correct", grade_source="manual")

    assert record["branch_correct"] is True
    assert record["answer_correct"] is True
    assert record["citation_valid"] is True
    assert record["sources"] == ["oag.ca.gov"]
    assert record["confidence"] == 0.5


def test_cache_serializes_pydantic_state(tmp_path, monkeypatch):
    monkeypatch.setattr("eval.run_eval.EVAL_ROOT", tmp_path)
    chunk = RetrievedChunk(
        chunk_id="gdpr:art33:p1",
        citation_label="GDPR Art. 33(1)",
        display_text="72 hours",
        similarity=0.9,
    )

    save_cache_file("answer_cache.json", {"T01:crag": {"retrieved": [chunk]}})

    assert (tmp_path / "answer_cache.json").exists()


def test_build_record_naive_has_no_branch_accuracy():
    item = EvalItem(
        qid="T01",
        split="test",
        category="covered",
        question="Breach deadline?",
        expected_branch="CORRECT",
        reference_points=["72 hours"],
    )
    payload = {
        "answer": "72 hours",
        "abstained": False,
        "sources": [],
        "confidence": 0.2,
        "citation_report": {"coverage": 0.0, "invalid_ids": []},
        "latency_ms": 100,
    }

    record = build_record(item, "naive", payload, grade="incorrect", grade_source="llm")

    assert record["branch_correct"] is None
    assert record["answer_correct"] is False
