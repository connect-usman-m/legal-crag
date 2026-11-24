import pytest

from app.graph.nodes.web_correct import rewrite_query
from app.llm.prompts import REWRITE_PROMPT_V1
from app.schemas.llm import RewriteOutput


class _FakeRewriter:
    def __init__(self, query):
        self.query = query

    async def ainvoke(self, prompt):
        self.prompt = prompt
        return RewriteOutput(query=self.query)


def test_rewrite_prompt_keeps_jurisdiction_instruction():
    assert "jurisdiction" in REWRITE_PROMPT_V1.lower()
    assert "keyword" in REWRITE_PROMPT_V1.lower()


@pytest.mark.asyncio
async def test_rewrite_does_not_inject_gdpr(monkeypatch):
    rewriter = _FakeRewriter("CCPA civil penalties amount per violation")
    monkeypatch.setattr("app.graph.nodes.web_correct.get_rewriter", lambda _settings=None: rewriter)

    query = await rewrite_query("What are the penalties for violating the CCPA?")

    assert query == "CCPA civil penalties amount per violation"
    assert "GDPR" not in query
    assert "CCPA" in rewriter.prompt
