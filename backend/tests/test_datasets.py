import json
from pathlib import Path

import pytest

from app.schemas.eval import EvalItem
from eval.judge_dev import calibration_rows, hand_labels, load_items, load_thresholds


@pytest.mark.parametrize("filename", ["dev_set.jsonl", "test_set.jsonl"])
def test_dataset_items_validate(filename):
    path = Path(__file__).resolve().parents[1] / "eval" / "datasets" / filename
    items = [EvalItem.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines()]

    assert items
    assert all(item.question.strip() for item in items)
    assert all(item.reference_points for item in items)


def test_dev_set_has_ten_items_and_443_split():
    path = Path(__file__).resolve().parents[1] / "eval" / "datasets" / "dev_set.jsonl"
    items = load_items(path)

    assert len(items) == 10
    assert sum(item.category == "covered" for item in items) == 4
    assert sum(item.category == "not_covered" for item in items) == 3
    assert sum(item.category == "ambiguous" for item in items) == 3


def test_calibrated_thresholds_are_ordered():
    thresholds = load_thresholds()

    assert thresholds == {
        "prompt_version": "V3",
        "lower_threshold": 0.5,
        "keep_threshold": 0.7,
        "upper_threshold": 0.9,
    }


@pytest.mark.slow
def test_hand_labels_cover_all_dev_retrieved_chunks():
    items = load_items(Path(__file__).resolve().parents[1] / "eval" / "datasets" / "dev_set.jsonl")

    assert len(hand_labels(items)) == 60


def test_calibration_rows_pair_judge_scores_with_human_labels():
    rows = calibration_rows(
        [
            {
                "qid": "D01",
                "chunk_scores": [
                    {"chunk_id": "gdpr:art33:p1", "score": 0.95, "verdict": "relevant"},
                    {"chunk_id": "gdpr:art83:p5", "score": 0.1, "verdict": "irrelevant"},
                ],
            }
        ],
        {("D01", "gdpr:art33:p1"): "relevant", ("D01", "gdpr:art83:p5"): "irrelevant"},
    )

    assert [(row["label"], row["score"]) for row in rows] == [("relevant", 0.95), ("irrelevant", 0.1)]
