import pytest

from app.graph.decision import decide, select_kept
from app.schemas.retrieval import ChunkScore


def _scores(values: list[float | None]) -> list[ChunkScore]:
    return [ChunkScore(chunk_id=f"gdpr:art{i}:p1", score=value) for i, value in enumerate(values, start=1)]


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([0.95, 0.2], "CORRECT"),
        ([0.7, 0.2], "CORRECT"),
        ([0.69, 0.31], "AMBIGUOUS"),
        ([0.3, 0.1], "AMBIGUOUS"),
        ([0.29, 0.1], "INCORRECT"),
        ([None, None], "AMBIGUOUS"),
        ([], "AMBIGUOUS"),
    ],
)
def test_decide_boundaries(values, expected):
    assert decide(_scores(values), upper=0.7, lower=0.3) == expected


def test_none_scores_are_ignored_when_deciding():
    assert decide(_scores([None, 0.8, 0.1]), upper=0.7, lower=0.3) == "CORRECT"


def test_select_kept_applies_keep_threshold_and_sets_flags():
    scores = _scores([0.8, 0.5, 0.49, None, 0.2])

    kept = select_kept(scores, keep=0.5)

    assert [score.chunk_id for score in kept] == ["gdpr:art1:p1", "gdpr:art2:p1"]
    assert [score.kept for score in scores] == [True, True, False, False, False]


def test_select_kept_handles_zero_kept():
    assert select_kept(_scores([0.4, 0.3]), keep=0.5) == []
