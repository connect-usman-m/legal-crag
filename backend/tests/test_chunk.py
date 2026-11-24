from app.ingest.chunk import build_chunks
from app.schemas.corpus import Chunk


def _article(article: int, paragraph: int, text: str, chapter: str = "I") -> dict:
    return {
        "source_id": "gdpr",
        "doc_type": "regulation_article",
        "chapter": chapter,
        "chapter_title": "General provisions",
        "section": None,
        "article": article,
        "article_title": "Lawfulness of processing",
        "paragraph": paragraph,
        "recital": None,
        "text": text,
    }


def test_article_paragraph_chunk_has_citation_label_breadcrumb_and_url():
    units = [_article(33, 1, "The controller shall notify the supervisory authority.")]

    chunks = build_chunks(units, token_counter=lambda text: len(text.split()))

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.chunk_id == "gdpr:art33:p1"
    assert chunk.citation_label == "GDPR Art. 33(1)"
    assert chunk.breadcrumb == "GDPR > Chapter I > Article 33 — Lawfulness of processing > (1)"
    assert "GDPR > Chapter I" in chunk.embed_text
    assert chunk.display_text == "The controller shall notify the supervisory authority."
    assert chunk.url == "https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_33"
    assert chunk.jurisdiction == "EU"
    Chunk.model_validate(chunk.model_dump())


def test_points_stay_with_parent_paragraph():
    units = [
        _article(
            6,
            1,
            "Processing shall be lawful if:\n(a) consent;\n(b) contract;\n(c) legal obligation.",
        )
    ]

    chunks = build_chunks(units, token_counter=lambda text: len(text.split()))

    assert [c.chunk_id for c in chunks] == ["gdpr:art6:p1"]
    assert "(a) consent;" in chunks[0].display_text
    assert "(c) legal obligation." in chunks[0].display_text


def test_oversized_paragraph_splits_on_point_boundaries():
    units = [
        _article(
            9,
            2,
            "Intro text.\n(a) first special category rule with many words here.\n"
            "(b) second special category rule with many words here.\n"
            "(c) third special category rule with many words here.",
        )
    ]

    chunks = build_chunks(units, token_counter=lambda text: len(text.split()), max_tokens=8)

    assert [c.chunk_id for c in chunks] == [
        "gdpr:art9:p2:part1",
        "gdpr:art9:p2:part2",
        "gdpr:art9:p2:part3",
    ]
    assert "(a)" in chunks[0].display_text
    assert "(b)" in chunks[1].display_text
    assert "(c)" in chunks[2].display_text


def test_recital_and_guideline_chunk_ids_and_labels():
    units = [
        {
            "source_id": "gdpr",
            "doc_type": "regulation_recital",
            "chapter": None,
            "chapter_title": None,
            "section": None,
            "article": None,
            "article_title": None,
            "paragraph": None,
            "recital": 85,
            "text": "Consent should be freely given.",
        },
        {
            "source_id": "edpb_consent_05_2020",
            "doc_type": "guideline_section",
            "chapter": None,
            "chapter_title": None,
            "section": None,
            "article": None,
            "article_title": None,
            "paragraph": None,
            "recital": None,
            "guideline_section": "2.1",
            "title": "Consent",
            "text": "Consent must be specific and informed.",
        },
    ]

    chunks = build_chunks(units, token_counter=lambda text: len(text.split()))

    assert [c.chunk_id for c in chunks] == ["gdpr:rec85", "edpb_consent_05_2020:s2.1:c01"]
    assert chunks[0].citation_label == "GDPR Recital 85"
    assert chunks[1].citation_label == "EDPB 05/2020 §2.1"
