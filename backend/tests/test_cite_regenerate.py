import pytest

from app.graph.nodes.cite import cite
from app.schemas.llm import GenerateOutput
from app.schemas.retrieval import ContextSource


class _FakeGenerator:
    def invoke(self, prompt):
        assert "Corrective instruction" in prompt
        return GenerateOutput(
            answer="Notify within 72 hours [S1].",
            used_source_ids=["S1"],
            abstained=False,
        )


@pytest.mark.asyncio
async def test_cite_regenerates_once_when_coverage_is_low(monkeypatch):
    monkeypatch.setattr("app.graph.nodes.cite.get_generator", lambda _settings=None: _FakeGenerator())
    state = {
        "question": "What is the deadline?",
        "draft_answer": "No citation here.",
        "retrieval_decision": "CORRECT",
        "context_sources": [
            ContextSource(
                sid="S1",
                kind="corpus",
                ref_id="gdpr:art33:p1",
                label="GDPR Art. 33(1)",
                url="https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_33",
                text="72 hours",
                relevance=0.95,
            )
        ],
    }

    result = await cite(state)

    assert result["answer"] == "Notify within 72 hours [S1]."
    assert result["warnings"] == []
    assert result["citation_report"]["coverage"] == 1.0
