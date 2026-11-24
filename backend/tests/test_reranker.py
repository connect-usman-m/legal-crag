import pytest

from app.retrieval.reranker import domain_trust, rerank_web_results
from app.schemas.retrieval import WebResult


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://eur-lex.europa.eu/eli/reg/2016/679/oj", 1.0),
        ("https://www.edpb.europa.eu/sites/default/files/file.pdf", 1.0),
        ("https://www.oag.ca.gov/privacy/ccpa", 1.0),
        ("https://ico.org.uk/action-weve-taken", 1.0),
        ("https://gdpr-info.eu/art-17-gdpr/", 0.6),
        ("https://iapp.org/news/a/article", 0.6),
        ("https://www.example-blog.com/post", 0.3),
    ],
)
def test_domain_trust_tiers(url, expected):
    assert domain_trust(url) == expected


def test_rerank_uses_cross_encoder_and_trust(monkeypatch):
    monkeypatch.setattr("app.retrieval.reranker.get_cross_encoder", lambda _model=None: _FakeCrossEncoder())
    results = [
        WebResult(
            result_id="web:aaa",
            url="https://example.com/a",
            domain="example.com",
            title="A",
            content="General discussion",
            tavily_score=0.5,
        ),
        WebResult(
            result_id="web:bbb",
            url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
            domain="eur-lex.europa.eu",
            title="GDPR Art. 33",
            content="72 hour notification rule",
            tavily_score=0.4,
        ),
    ]

    ranked = rerank_web_results("breach deadline", results, model="fake")

    assert [result.result_id for result in ranked] == ["web:bbb", "web:aaa"]
    assert all(0 <= result.final_score <= 1 for result in ranked)
    assert ranked[0].rerank_score > ranked[1].rerank_score


class _FakeCrossEncoder:
    def predict(self, pairs):
        return [8.0 if "72 hour" in text else -2.0 for _, text in pairs]
