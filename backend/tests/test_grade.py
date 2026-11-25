from app.schemas.eval import EvalItem
from eval.grade import apply_manual_overrides, grade_values


def _item():
    return EvalItem(
        qid="T06",
        split="test",
        category="not_covered",
        question="What are the CCPA penalties?",
        expected_branch="INCORRECT",
        reference_points=["Civil penalties per violation"],
    )


class _FakeGrader:
    def __init__(self, verdict="correct", unsupported_claims=0):
        self.verdict = verdict
        self.unsupported_claims = unsupported_claims

    def invoke(self, _prompt):
        from app.schemas.llm import GradeOutput

        return GradeOutput(
            verdict=self.verdict,
            unsupported_claims=self.unsupported_claims,
            rationale="Checked against sources",
        )


def test_grade_values_uses_llm_verdict_and_reference_points():
    values = grade_values(_item(), _FakeGrader("correct", 0), abstained=False, acceptable_abstain=False)

    assert values["grade"] == "correct"
    assert values["answer_correct"] is True
    assert values["grade_source"] == "llm"
    assert values["unsupported_claims"] == 0


def test_abstention_counts_only_when_acceptable():
    item = _item()
    item.acceptable_abstain = True

    assert grade_values(item, _FakeGrader("abstained", 0), True, True)["answer_correct"] is True
    assert grade_values(_item(), _FakeGrader("abstained", 0), True, False)["answer_correct"] is False


def test_manual_override_wins():
    records = [{"qid": "T06", "mode": "naive", "grade": "correct", "answer_correct": True}]
    overrides = [
        {
            "qid": "T06",
            "mode": "naive",
            "grade": "incorrect",
            "note": "Unsupported fine amount",
        }
    ]

    updated = apply_manual_overrides(records, overrides)

    assert updated[0]["grade"] == "incorrect"
    assert updated[0]["grade_source"] == "manual"
    assert updated[0]["answer_correct"] is False
