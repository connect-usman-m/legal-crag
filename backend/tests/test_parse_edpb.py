import pymupdf

from app.ingest.parse_edpb import parse_edpb_document, section_text_to_units


def _pdf_with_blocks(blocks: list[tuple[str, float, int]], tmp_path) -> str:
    path = tmp_path / "edpb_fixture.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    y = 40
    for text, size, flags in blocks:
        page.insert_text((40, y), text, fontsize=size)
        y += size + 8
    doc.save(path)
    doc.close()
    return str(path)


def test_font_size_headings_define_sections_and_strip_page_furniture(tmp_path):
    path = _pdf_with_blocks(
        [
            ("EDPB Guidelines 05/2020 on consent", 16, 0),
            ("1. Introduction", 12, 0),
            ("This is the introduction body.", 10, 0),
            ("2. Scope", 12, 0),
            ("This is the scope body.", 10, 0),
            ("4.5.2016", 8, 0),
            ("L 119/1", 8, 0),
            ("Official Journal of the European Union", 8, 0),
            ("EN", 8, 0),
        ],
        tmp_path,
    )

    sections = parse_edpb_document(path, "edpb_consent_05_2020")

    assert [s["section"] for s in sections] == ["1", "2"]
    assert sections[0]["title"] == "Introduction"
    assert "This is the introduction body." in sections[0]["text"]
    assert all("Official Journal" not in s["text"] for s in sections)


def test_sections_become_units_with_stable_section_paths():
    units = section_text_to_units(
        [
            {
                "section": "2.1",
                "title": "Consent",
                "text": "Consent must be freely given and specific.",
            }
        ],
        "edpb_consent_05_2020",
    )

    assert units[0]["guideline_section"] == "2.1"
    assert units[0]["source_id"] == "edpb_consent_05_2020"
    assert units[0]["doc_type"] == "guideline_section"
