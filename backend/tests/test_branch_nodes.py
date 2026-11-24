import pytest

from app.graph.nodes.filter_supplement import filter_and_supplement
from app.graph.nodes.passthrough import passthrough
from app.graph.nodes.web_correct import web_correct
from app.schemas.retrieval import ChunkScore, RetrievedChunk, WebResult

QUESTION = "What are the penalties for violating the CCPA?"


def _chunk(chunk_id="gdpr:art83:p5", score=0.1):
    return RetrievedChunk(
        chunk_id=chunk_id,
        citation_label="GDPR Art. 83(5)",
        url="https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_83",
        display_text="GDPR fines",
        source_id="gdpr",
        doc_type="regulation_article",
        similarity=0.5,
    )


def _score(chunk_id="gdpr:art83:p5", score=0.1, kept=False):
    return ChunkScore(chunk_id=chunk_id, score=score, kept=kept)


def _web_result():
    return WebResult(
        result_id="web:abc",
        url="https://oag.ca.gov/privacy/ccpa",
        domain="oag.ca.gov",
        title="CCPA penalties",
        content="Civil penalties per violation",
        rerank_score=0.9,
        domain_trust=1.0,
        final_score=0.92,
        retrieved_at="2026-11-24T00:00:00Z",
    )


def _patch_web(monkeypatch, results=None, error=False):
    async def fake_rewrite(_question, _settings=None):
        return "CCPA civil penalties amount per violation"

    def fake_search(_query, _settings=None):
        if error:
            raise RuntimeError("Tavily down")
        return results if results is not None else [_web_result()]

    monkeypatch.setattr("app.graph.nodes.web_correct.rewrite_query", fake_rewrite)
    monkeypatch.setattr("app.graph.nodes.filter_supplement.rewrite_query", fake_rewrite)
    monkeypatch.setattr("app.graph.nodes.web_correct.search_web", fake_search)
    monkeypatch.setattr("app.graph.nodes.filter_supplement.search_web", fake_search)


def test_passthrough_keeps_corpus_only():
    result = passthrough(
        {"retrieved": [_chunk()], "chunk_scores": [_score(score=0.95)]},
        keep=0.7,
    )

    assert [source.kind for source in result["context_sources"]] == ["corpus"]
    assert result["context_sources"][0].sid == "S1"
    assert result["context_sources"][0].ref_id == "gdpr:art83:p5"
    assert result["chunk_scores"][0].kept is True


@pytest.mark.asyncio
async def test_web_correct_discards_corpus_and_uses_web(monkeypatch):
    _patch_web(monkeypatch)

    result = await web_correct({"question": QUESTION, "retrieved": [_chunk()]}, web_top_n=3)

    assert [source.kind for source in result["context_sources"]] == ["web"]
    assert result["context_sources"][0].label == "oag.ca.gov"
    assert result["web_query"] == "CCPA civil penalties amount per violation"
    assert result["warnings"] == []


@pytest.mark.asyncio
async def test_web_correct_failure_returns_empty_context(monkeypatch):
    _patch_web(monkeypatch, error=True)

    result = await web_correct({"question": QUESTION, "retrieved": []}, web_top_n=3)

    assert result["context_sources"] == []
    assert result["warnings"] == ["web_search_failed"]


@pytest.mark.asyncio
async def test_filter_supplement_merges_kept_corpus_and_web(monkeypatch):
    _patch_web(monkeypatch)
    kept = RetrievedChunk(
        chunk_id="gdpr:art33:p1",
        citation_label="GDPR Art. 33(1)",
        url="https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_33",
        display_text="72 hours",
        source_id="gdpr",
        doc_type="regulation_article",
        similarity=0.8,
    )

    result = await filter_and_supplement(
        {
            "question": "GDPR 72 hours versus HIPAA",
            "retrieved": [kept, _chunk()],
            "chunk_scores": [_score("gdpr:art33:p1", 0.8, True), _score("gdpr:art83:p5", 0.1)],
        },
        keep=0.7,
        web_n=2,
    )

    assert [source.kind for source in result["context_sources"]] == ["corpus", "web"]
    assert [source.sid for source in result["context_sources"]] == ["S1", "S2"]


@pytest.mark.asyncio
async def test_filter_supplement_zero_kept_warns(monkeypatch):
    _patch_web(monkeypatch)

    result = await filter_and_supplement(
        {"question": QUESTION, "retrieved": [], "chunk_scores": []},
        keep=0.7,
        web_n=2,
    )

    assert [source.kind for source in result["context_sources"]] == ["web"]
    assert result["warnings"] == ["no_corpus_chunks_above_keep"]
