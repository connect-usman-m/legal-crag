import pytest

from app.graph.nodes.generate import generate, render_sources
from app.schemas.retrieval import ContextSource


class _FakeGenerator:
    def invoke(self, _prompt):
        class _Response:
            content = "Notify within 72 hours [S1]."

        return _Response()


@pytest.mark.asyncio
async def test_generate_uses_context_and_records_used_sources(monkeypatch):
    monkeypatch.setattr("app.graph.nodes.generate.get_generator", lambda _settings=None: _FakeGenerator())
    sources = [
        ContextSource(
            sid="S1",
            kind="corpus",
            ref_id="gdpr:art33:p1",
            label="GDPR Art. 33(1)",
            url="https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_33",
            text="72 hours",
            relevance=0.95,
        )
    ]

    result = await generate({"question": "What is the deadline?", "context_sources": sources})

    assert result["used_source_ids"] == ["S1"]
    assert result["abstained"] is False
    assert result["generation_attempts"] == 1
    assert "[S1] (corpus) GDPR Art. 33(1)" in render_sources(sources)


@pytest.mark.asyncio
async def test_generate_forces_abstention_without_sources():
    result = await generate({"question": "q", "context_sources": []})

    assert result["abstained"] is True
    assert result["used_source_ids"] == []
    assert result["generation_attempts"] == 0
