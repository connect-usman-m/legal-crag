from app.ingest.parse_gdpr import parse_gdpr_text


def test_parses_article_paragraphs_points_and_recitals():
    text = """
(1)
The first recital.
(2)
The second recital.
HAVE ADOPTED THIS REGULATION:
CHAPTER I
General provisions
Article 1
Subject-matter and objectives
1.
This Regulation lays down rules.
2.
It applies to everyone.
Article 6
Lawfulness of processing
1.
Processing shall be lawful only if:
(a)  the data subject has given consent;
(b)  processing is necessary for a contract;
2.
Member States may add provisions.
"""

    units = parse_gdpr_text(text)

    recitals = [u for u in units if u["doc_type"] == "regulation_recital"]
    articles = [u for u in units if u["doc_type"] == "regulation_article"]
    article_one = [u for u in articles if u["article"] == 1]

    assert [u["recital"] for u in recitals] == [1, 2]
    assert recitals[0]["text"] == "The first recital."
    assert [u["paragraph"] for u in article_one] == [1, 2]
    assert article_one[0]["article_title"] == "Subject-matter and objectives"
    assert article_one[0]["chapter"] == "I"
    assert article_one[0]["chapter_title"] == "General provisions"
    art6 = [u for u in articles if u["article"] == 6]
    assert [u["paragraph"] for u in art6] == [1, 2]
    assert "(a)  the data subject has given consent;" in art6[0]["text"]
    assert "(b)  processing is necessary for a contract;" in art6[0]["text"]
    assert all(u["jurisdiction"] == "EU" for u in units)


def test_ignores_footer_and_footnote_lines():
    text = """
(1)
A recital continued over two lines.
4.5.2016   L 119/1   Official Journal of the European Union   EN
(1) OJ C 229, 31.7.2012, p. 90.
HAVE ADOPTED THIS REGULATION:
Article 1
Subject-matter
1.
Body text.
"""

    units = parse_gdpr_text(text)

    assert len([u for u in units if u["doc_type"] == "regulation_recital"]) == 1
    recital = next(u for u in units if u["doc_type"] == "regulation_recital")
    assert "Official Journal" not in recital["text"]
    assert "OJ C 229" not in recital["text"]
