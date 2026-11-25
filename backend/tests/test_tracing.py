from app.core.config import Settings
from app.core.tracing import apply_trace_metadata


class _FakeRunTree:
    def __init__(self):
        self.metadata = {}
        self.tags = []

    def add_metadata(self, values):
        self.metadata.update(values)

    def add_tags(self, values):
        self.tags.extend(values)


def test_apply_trace_metadata_sets_decision_and_tag():
    run = _FakeRunTree()
    result = {
        "retrieval_decision": "INCORRECT",
        "chunk_scores": [{"score": 0.2, "kept": False}],
        "web_results": [{"result_id": "web:abc"}],
        "abstained": False,
        "confidence": 0.4,
        "citation_report": {"coverage": 0.9},
        "warnings": [],
    }

    settings = Settings(_env_file=None, groq_api_key="test", tavily_api_key="test", chroma_collection="gdpr_v2")
    apply_trace_metadata(
        run,
        {"request_id": "req-1", "mode": "crag"},
        result,
        settings,
        upper=0.7,
        lower=0.3,
        keep=0.5,
    )

    assert run.metadata["retrieval_decision"] == "INCORRECT"
    assert run.metadata["max_chunk_score"] == 0.2
    assert run.metadata["kept_chunks"] == 0
    assert run.metadata["web_results_used"] == 1
    assert run.tags == ["mode:crag", "decision:INCORRECT"]
    assert run.metadata["corpus_version"] == "gdpr_v2"
    assert run.metadata["prompt_versions"]["evaluator"] == "V3"
