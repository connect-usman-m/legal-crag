import json
import re
from pathlib import Path

import pymupdf

from app.core.config import Settings

HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")
JOURNAL_FURNITURE = re.compile(
    r"^(?:\d{1,2}\.\d{1,2}\.\d{4}|L\s*\d+\s*/\s*\d+|Official Journal of the European Union|EN|\d{1,3})$"
)
VERSION_DATES = {
    "edpb_consent_05_2020": "2020-07-28",
    "edpb_breach_09_2022": "2023-04-06",
    "edpb_access_01_2022": "2023-04-06",
}
INSTRUMENTS = {
    "edpb_consent_05_2020": "EDPB Guidelines 05/2020 on consent",
    "edpb_breach_09_2022": "EDPB Guidelines 9/2022 on personal data breach notification",
    "edpb_access_01_2022": "EDPB Guidelines 01/2022 on data subject rights: right of access",
}


def parse_edpb_document(path: str, source_id: str) -> list[dict]:
    heights: list[float] = []
    with pymupdf.open(path) as document:
        for page in document:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        if span["text"].strip():
                            heights.append(span["size"])
    body_size = sorted(heights)[len(heights) // 2] if heights else 10.0

    sections: list[dict] = []
    current: dict | None = None
    with pymupdf.open(path) as document:
        for page in document:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    text = " ".join(span["text"].strip() for span in line["spans"]).strip()
                    if not text or JOURNAL_FURNITURE.match(text):
                        continue
                    size = max((span["size"] for span in line["spans"]), default=body_size)
                    bold = any(span["flags"] & 16 for span in line["spans"])
                    match = HEADING.match(text) if size >= body_size or bold else None
                    if match and size >= body_size:
                        if current:
                            sections.append(current)
                        current = {
                            "source_id": source_id,
                            "section": match.group(1),
                            "title": match.group(2),
                            "text": "",
                        }
                    elif current:
                        current["text"] += (" " if current["text"] else "") + text
    if current:
        sections.append(current)
    merged: dict[str, dict] = {}
    for section in sections:
        key = section["section"]
        if key in merged:
            merged[key]["text"] += " " + section["text"]
        else:
            merged[key] = section
    return list(merged.values())


def section_text_to_units(sections: list[dict], source_id: str) -> list[dict]:
    units = []
    for section in sections:
        units.append(
            {
                "source_id": source_id,
                "doc_type": "guideline_section",
                "chapter": None,
                "chapter_title": None,
                "section": section.get("section"),
                "article": None,
                "article_title": None,
                "paragraph": None,
                "recital": None,
                "guideline_section": section.get("section"),
                "title": section.get("title"),
                "text": section["text"],
                "version_date": VERSION_DATES[source_id],
                "instrument": INSTRUMENTS[source_id],
            }
        )
    return units


def main() -> None:
    settings = Settings()
    raw_dir = Path(settings.chroma_dir).parent.parent / "data" / "raw"
    processed_dir = raw_dir.parent / "processed"
    for source_id in VERSION_DATES:
        path = raw_dir / f"{source_id}.pdf"
        if not path.exists():
            raise FileNotFoundError(f"Missing raw source: {path}")
        sections = parse_edpb_document(str(path), source_id)
        units = section_text_to_units(sections, source_id)
        output = processed_dir / f"{source_id}_units.jsonl"
        output.write_text(
            "\n".join(json.dumps(unit, ensure_ascii=False) for unit in units) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {len(units)} units to {output}")


if __name__ == "__main__":
    main()
