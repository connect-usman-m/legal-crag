import pytest

from app.graph.nodes.evaluate import evaluate_chunks
from app.llm.prompts import EVALUATOR_PROMPT_V1
from app.schemas.llm import JudgeOutput
from app.schemas.retrieval import RetrievedChunk


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    monkeypatch.setattr("app.graph.nodes.evaluate.load_cache", lambda: {})
    monkeypatch.setattr("app.graph.nodes.evaluate.save_cache", lambda _cache: None)


def test_evaluator_prompt_has_anchored_bands_and_jurisdiction_rule():
    assert "0.9" in EVALUATOR_PROMPT_V1
    assert "0.6" in EVALUATOR_PROMPT_V1
    assert "0.3" in EVALUATOR_PROMPT_V1
    assert "jurisdiction" in EVALUATOR_PROMPT_V1.lower()
    assert EVALUATOR_PROMPT_V1.count("Example") >= 3


class _FakeStructuredJudge:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.configs = []

    async def ainvoke(self, _prompt):
        from asyncio import sleep

        await sleep(0)
        return next(self.outputs)

    async def abatch(self, _prompts, config=None, return_exceptions=False):
        from asyncio import sleep

        await sleep(0)
        self.configs.append(config)
        return [next(self.outputs) for _ in _prompts]


class _FlakyStructuredJudge:
    def __init__(self):
        self.calls = 0
        self.retries = 0

    async def abatch(self, prompts, config=None, return_exceptions=False):
        self.calls += 1
        if self.calls == 1:
            return [RuntimeError("rate limited") for _ in prompts]
        return [JudgeOutput(score=0.9, verdict="relevant", reason="ok", jurisdiction_match=True) for _ in prompts]

    async def ainvoke(self, _prompt):
        self.retries += 1
        return JudgeOutput(score=0.9, verdict="relevant", reason="ok", jurisdiction_match=True)


@pytest.mark.asyncio
async def test_evaluate_scores_each_chunk_and_sets_decision(monkeypatch):
    judge = _FakeStructuredJudge(
        [
            JudgeOutput(score=0.95, verdict="relevant", reason="direct rule", jurisdiction_match=True),
            JudgeOutput(score=0.1, verdict="irrelevant", reason="wrong jurisdiction", jurisdiction_match=False),
        ]
    )
    monkeypatch.setattr("app.graph.nodes.evaluate.get_judge", lambda _settings=None: judge)

    state = {
        "question": "What are the penalties for violating the CCPA?",
        "retrieved": [
            {
                "chunk_id": "gdpr:art83:p5",
                "citation_label": "GDPR Art. 83(5)",
                "display_text": "Fines under GDPR",
                "similarity": 0.5,
            },
            {
                "chunk_id": "oag:ccpa",
                "citation_label": "oag.ca.gov",
                "display_text": "CCPA penalties",
                "similarity": 0.4,
            },
        ],
    }

    result = await evaluate_chunks(state)

    assert [score.score for score in result["chunk_scores"]] == [0.95, 0.1]
    assert result["retrieval_decision"] == "CORRECT"
    assert result["decision_reason"]
    assert judge.configs == [{"max_concurrency": 6}]
    assert result["prompt_versions"] == {"evaluator": "V3"}


@pytest.mark.asyncio
async def test_evaluate_accepts_pydantic_retrieved_chunks(monkeypatch):
    judge = _FakeStructuredJudge([JudgeOutput(score=0.9, verdict="relevant", reason="exact", jurisdiction_match=True)])
    monkeypatch.setattr("app.graph.nodes.evaluate.get_judge", lambda _settings=None: judge)
    chunk = RetrievedChunk(
        chunk_id="gdpr:art33:p1",
        citation_label="GDPR Art. 33(1)",
        display_text="72 hours",
        similarity=0.9,
    )

    result = await evaluate_chunks({"question": "Deadline?", "retrieved": [chunk]})

    assert result["chunk_scores"][0].chunk_id == "gdpr:art33:p1"


@pytest.mark.asyncio
async def test_evaluate_retries_failed_batch_once(monkeypatch):
    judge = _FlakyStructuredJudge()
    monkeypatch.setattr("app.graph.nodes.evaluate.get_judge", lambda _settings=None: judge)
    state = {
        "question": "What is the right to erasure?",
        "retrieved": [{"chunk_id": "gdpr:art17:p1", "citation_label": "GDPR Art. 17(1)", "display_text": "Erasure"}],
    }

    result = await evaluate_chunks(state)

    assert judge.calls == 1
    assert judge.retries == 1
    assert result["chunk_scores"][0].score == 0.9
