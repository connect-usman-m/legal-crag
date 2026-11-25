from app.graph.confidence import compute_confidence
from app.schemas.retrieval import ContextSource


def _source(sid: str, relevance: float, kind: str = "corpus") -> ContextSource:
    return ContextSource(
        sid=sid,
        kind=kind,
        ref_id=sid,
        label=sid,
        url="https://example.com",
        text="text",
        relevance=relevance,
    )


def test_confidence_uses_evidence_coverage_and_source_factor():
    value, label = compute_confidence(
        cited_sources=[_source("S1", 0.9), _source("S2", 0.8, "web")],
        decision="CORRECT",
        coverage=1.0,
        abstained=False,
    )

    assert value == 0.85
    assert label == "High"


def test_confidence_applies_web_only_factor_and_low_coverage_penalty():
    value, label = compute_confidence(
        cited_sources=[_source("S1", 0.9, "web")],
        decision="INCORRECT",
        coverage=0.8,
        abstained=False,
        low_coverage=True,
    )

    assert value == 0.25
    assert label == "Low"


def test_abstention_zeroes_confidence():
    value, label = compute_confidence([], "CORRECT", 1.0, abstained=True)

    assert value == 0.0
    assert label == "None"
