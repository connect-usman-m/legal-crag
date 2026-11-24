from app.pipelines.naive_rag import parse_citations, render_context


def _results():
    return [
        {
            "chunk_id": "gdpr:art33:p1",
            "metadata": {"citation_label": "GDPR Art. 33(1)"},
            "display_text": "The controller shall notify the supervisory authority without undue delay.",
            "similarity": 0.9,
        },
        {
            "chunk_id": "gdpr:art33:p2",
            "metadata": {"citation_label": "GDPR Art. 33(2)"},
            "display_text": "The notification shall include the nature of the breach.",
            "similarity": 0.7,
        },
    ]


def test_render_context_numbers_sources_with_type_and_label():
    context = render_context(_results())

    assert "[S1] (corpus) GDPR Art. 33(1)" in context
    assert "[S2] (corpus) GDPR Art. 33(2)" in context
    assert "without undue delay" in context
    assert "nature of the breach" in context


def test_parse_citations_keeps_only_cited_sources():
    answer = "Notify within 72 hours [S1]. Additional detail [S1][S2]."

    cited = parse_citations(answer, _results())

    assert [result["chunk_id"] for result in cited] == ["gdpr:art33:p1", "gdpr:art33:p2"]


def test_parse_citations_drops_invalid_markers():
    answer = "Notify within 72 hours [S1] and [S9]."

    cited = parse_citations(answer, _results())

    assert [result["chunk_id"] for result in cited] == ["gdpr:art33:p1"]
