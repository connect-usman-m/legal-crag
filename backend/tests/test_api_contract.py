import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.schemas.retrieval import ContextSource


def _settings(**overrides):
    return Settings(
        _env_file=None,
        groq_api_key="test-groq",
        tavily_api_key="test-tavily",
        rate_limit="1000/minute",
        langsmith_tracing=False,
        **overrides,
    )


class _FakeGraph:
    async def ainvoke(self, state, config=None):
        return {
            "question": state["question"],
            "retrieval_decision": "CORRECT",
            "decision_reason": "max=0.95 (gdpr:art33:p1)",
            "answer": "Notify within 72 hours [S1].",
            "abstained": False,
            "sources": [
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
            "citation_report": {
                "valid_ids": ["S1"],
                "invalid_ids": [],
                "unused_ids": [],
                "factual_sentences": 1,
                "cited_sentences": 1,
                "coverage": 1.0,
            },
            "confidence": 0.95,
            "confidence_label": "High",
            "chunk_scores": [
                {
                    "chunk_id": "gdpr:art33:p1",
                    "label": "GDPR Art. 33(1)",
                    "score": 0.95,
                    "verdict": "relevant",
                    "reason": "exact rule",
                    "kept": True,
                }
            ],
            "warnings": [],
        }


class _FakeRuntime:
    def __init__(self, settings):
        self.settings = settings
        self.graph = _FakeGraph()


@pytest.fixture
def client():
    settings = _settings()
    app = create_app(settings, runtime=_FakeRuntime(settings))
    return TestClient(app)


def test_query_returns_full_response(client):
    response = client.post("/query", json={"question": "What is the breach deadline?"})

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "crag"
    assert body["retrieval_decision"] == "CORRECT"
    assert body["sources"][0]["label"] == "GDPR Art. 33(1)"
    assert body["chunk_scores"][0]["score"] == 0.95
    assert body["trace_id"]
    assert body["models"]["judge"] == "openai/gpt-oss-20b"
    assert body["thresholds"] == {"upper": 0.7, "lower": 0.3, "keep": 0.5}
    assert body["timings_ms"] is None


def test_query_debug_includes_timings(client):
    body = client.post("/query", json={"question": "What is the deadline?", "debug": True}).json()

    assert body["timings_ms"] == {"total": body["latency_ms"]}


def test_query_validation_error_envelope(client):
    response = client.post("/query", json={"question": "x"})

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_query_uses_request_runtime(monkeypatch):
    settings = _settings()
    app = create_app(settings, runtime=_FakeRuntime(settings))
    seen = []

    async def fake_crag(state, settings, runtime):
        seen.append(runtime)
        return {"answer": "scoped", "sources": [], "retrieval_decision": "CORRECT"}

    monkeypatch.setattr("app.api.routes_query.run_crag_query", fake_crag)

    assert TestClient(app).post("/query", json={"question": "What is the deadline?"}).status_code == 200
    assert seen == [app.state.runtime]


def test_compare_calls_both_modes(monkeypatch):
    settings = _settings()
    app = create_app(settings, runtime=_FakeRuntime(settings))

    calls = []

    async def fake_crag(state, settings, runtime):
        calls.append("crag")
        return {"answer": "crag", "sources": [], "retrieval_decision": "CORRECT"}

    async def fake_naive(state, settings, runtime):
        calls.append("naive")
        return {"answer": "naive", "sources": [], "retrieval_decision": None}

    monkeypatch.setattr("app.api.routes_query.run_crag_query", fake_crag)
    monkeypatch.setattr("app.api.routes_query.run_naive_query", fake_naive)

    body = TestClient(app).post("/compare", json={"question": "What is the deadline?"}).json()

    assert set(calls) == {"crag", "naive"}
    assert body["crag"]["answer"] == "crag"
    assert body["naive"]["answer"] == "naive"


def test_query_requires_demo_key_when_configured():
    settings = _settings(demo_api_key="secret")
    app = create_app(settings, runtime=_FakeRuntime(settings))

    denied = TestClient(app).post("/query", json={"question": "What is the deadline?"})
    allowed = TestClient(app).post(
        "/query",
        json={"question": "What is the deadline?"},
        headers={"X-API-Key": "secret"},
    )

    assert denied.status_code == 401
    assert denied.json()["error"] == "unauthorized"
    assert allowed.status_code == 200


def test_openapi_contract(client):
    schema = client.get("/openapi.json").json()

    assert "/query" in schema["paths"]
    assert "/compare" in schema["paths"]
    assert "QueryResponse" in schema["components"]["schemas"]
