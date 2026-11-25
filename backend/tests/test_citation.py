import pytest

from app.graph.nodes.cite import (
    citation_report,
    factual_sentences,
    normalize_answer,
    renumber_answer,
)


def test_normalize_answer_accepts_unicode_markers():
    assert normalize_answer("Answer 【S1】 and [S2].") == "Answer [S1] and [S2]."


def test_factual_sentences_excludes_headings_disclaimers_and_abstain():
    text = (
        "Answer [S1].\nNot legal advice.\nThis is general information, not legal advice.\n"
        "It does not constitute legal advice.\nNOT ENOUGH EVIDENCE: nothing found.\nAnother fact [S2]."
    )

    sentences = factual_sentences(text)

    assert sentences == ["Answer [S1].", "Another fact [S2]."]


def test_citation_report_detects_invalid_unused_and_coverage():
    answer = "One [S1]. Two [S9]. Three."
    sources = [{"sid": "S1"}, {"sid": "S2"}]

    report = citation_report(answer, sources)

    assert report["valid_ids"] == ["S1"]
    assert report["invalid_ids"] == ["S9"]
    assert report["unused_ids"] == ["S2"]
    assert report["factual_sentences"] == 3
    assert report["cited_sentences"] == 1
    assert report["coverage"] == pytest.approx(1 / 3)


def test_renumber_answer_preserves_first_use_order():
    assert renumber_answer("B [S2], A [S1], B again [S2].", ["S2", "S1"]) == "B [S1], A [S2], B again [S1]."
