import json
import re
from pathlib import Path

import pymupdf

from app.core.config import Settings

ARTICLE_HEADING = re.compile(r"^Article\s+(\d{1,3})[\s.:;-]*$")
RECITAL_NUMBER = re.compile(r"^\((\d{1,3})\)\s*(.*)$")
PARAGRAPH_NUMBER = re.compile(r"^(\d{1,3})\.$")
PAREN_PARAGRAPH = re.compile(r"^\((\d{1,3})\)\s")
ARTICLE_PAREN_PARAGRAPHS = {4, 5, 12, 42, 43, 60, 79, 89}
POINT = re.compile(r"^\([a-z]\)\s")
CHAPTER_HEADING = re.compile(r"^CHAPTER\s+([IVX]+)$")
SECTION_HEADING = re.compile(r"^Section\s+(\d{1,2})$")
JOURNAL_FURNITURE = re.compile(
    r"^(?:\d{1,2}\.\d{1,2}\.\d{4}|L\s*\d+\s*/\s*\d+|Official Journal of the European Union|EN)$"
)
FOOTNOTE = re.compile(
    r"^\(\d+\)\s+(?:OJ C \d+|OJ L \d+|Position of the European Parliament|"
    r"Council Regulation|Commission Recommendation|Directive \d{4}/\d+/\d+ of \d)"
)


def _clean_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or FOOTNOTE.match(line):
            continue
        if JOURNAL_FURNITURE.match(line) or "Official Journal of the European Union" in line:
            continue
        lines.append(line)
    return lines


def parse_gdpr_text(text: str) -> list[dict]:
    lines = _clean_lines(text)
    units: list[dict] = []
    chapter: str | None = None
    chapter_title: str | None = None
    section: str | None = None
    in_articles = False
    article: int | None = None
    article_title = ""
    paragraph: int | None = None
    buffer: list[str] = []
    recital: int | None = None
    recital_buffer: list[str] = []

    title_line_index: int | None = None

    def flush_paragraph() -> None:
        nonlocal buffer
        if paragraph is not None and article is not None and buffer:
            units.append(
                {
                    "source_id": "gdpr",
                    "jurisdiction": "EU",
                    "doc_type": "regulation_article",
                    "chapter": chapter,
                    "chapter_title": chapter_title,
                    "section": section,
                    "article": article,
                    "article_title": article_title,
                    "paragraph": paragraph,
                    "recital": None,
                    "text": " ".join(buffer),
                }
            )
        buffer = []

    def flush_recital() -> None:
        nonlocal recital_buffer
        if recital is not None and recital_buffer:
            units.append(
                {
                    "source_id": "gdpr",
                    "jurisdiction": "EU",
                    "doc_type": "regulation_recital",
                    "chapter": None,
                    "chapter_title": None,
                    "section": None,
                    "article": None,
                    "article_title": None,
                    "paragraph": None,
                    "recital": recital,
                    "text": " ".join(recital_buffer),
                }
            )
        recital_buffer = []

    for index, line in enumerate(lines):
        if title_line_index is not None and title_line_index < index:
            title_line_index = None
        if line == "HAVE ADOPTED THIS REGULATION:":
            flush_recital()
            in_articles = True
            continue

        recital_match = RECITAL_NUMBER.match(line)
        if not in_articles and recital_match:
            flush_recital()
            recital = int(recital_match.group(1))
            inline = recital_match.group(2).strip()
            recital_buffer = [inline] if inline else []
            continue

        if not in_articles:
            if recital is not None:
                recital_buffer.append(line)
            continue

        chapter_match = CHAPTER_HEADING.match(line)
        if chapter_match:
            flush_paragraph()
            paragraph = None
            chapter = chapter_match.group(1)
            chapter_title = lines[index + 1] if index + 1 < len(lines) else None
            section = None
            continue

        section_match = SECTION_HEADING.match(line)
        if section_match:
            flush_paragraph()
            paragraph = None
            section = section_match.group(1)
            continue

        article_match = ARTICLE_HEADING.match(line)
        if article_match:
            flush_paragraph()
            paragraph = None
            buffer = []
            article = int(article_match.group(1))
            article_title = lines[index + 1] if index + 1 < len(lines) else ""
            if (
                len(article_title) <= 100
                and not PARAGRAPH_NUMBER.match(article_title)
                and not ARTICLE_HEADING.match(article_title)
            ):
                title_line_index = index + 1
                paragraph = 1
            else:
                paragraph = 1
            continue

        if (
            title_line_index == index
            and not ARTICLE_HEADING.match(line)
            and not CHAPTER_HEADING.match(line)
            and not SECTION_HEADING.match(line)
        ):
            title_line_index = None
            continue

        paragraph_match = PARAGRAPH_NUMBER.match(line)
        if paragraph_match and article is not None:
            flush_paragraph()
            paragraph = int(paragraph_match.group(1))
            continue

        paren_match = PAREN_PARAGRAPH.match(line)
        if paren_match and article is not None and article not in ARTICLE_PAREN_PARAGRAPHS:
            flush_paragraph()
            paragraph = int(paren_match.group(1))
            continue

        if paragraph is None and article is not None:
            if POINT.match(line):
                paragraph = 1
                buffer.append(line)
            continue

        if buffer and (POINT.match(line) or line[0].islower()):
            buffer.append(line)
        else:
            buffer.append(line)

    flush_paragraph()
    flush_recital()
    deduplicated: list[dict] = []
    seen_recitals: set[int] = set()
    for unit in units:
        number = unit.get("recital")
        if number is not None:
            if number in seen_recitals:
                continue
            seen_recitals.add(number)
        deduplicated.append(unit)
    return deduplicated


def parse_gdpr_file(path: Path) -> list[dict]:
    if path.suffix.lower() == ".pdf":
        with pymupdf.open(path) as document:
            text = "\n".join(page.get_text() for page in document)
    else:
        from bs4 import BeautifulSoup

        text = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").get_text("\n")
    return parse_gdpr_text(text)


def main() -> None:
    settings = Settings()
    raw_dir = Path(settings.chroma_dir).parent.parent / "data" / "raw"
    processed_dir = raw_dir.parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    source = next(
        (p for p in (raw_dir / "gdpr.html", raw_dir / "gdpr.pdf") if p.exists()),
        None,
    )
    if source is None:
        raise FileNotFoundError("GDPR raw source not found in data/raw")
    units = parse_gdpr_file(source)
    if len({u["article"] for u in units if u["article"] is not None}) != 99:
        raise ValueError("Expected 99 GDPR articles")
    if len([u for u in units if u["recital"] is not None]) != 173:
        raise ValueError("Expected 173 GDPR recitals")
    output = processed_dir / "gdpr_units.jsonl"
    output.write_text(
        "\n".join(json.dumps(unit, ensure_ascii=False) for unit in units) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(units)} GDPR units to {output}")


if __name__ == "__main__":
    main()
