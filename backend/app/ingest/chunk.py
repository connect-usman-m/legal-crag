import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from app.schemas.corpus import Chunk

POINT = re.compile(r"^\([a-z]\)\s")
INSTRUMENTS = {
    "gdpr": "Regulation (EU) 2016/679 (GDPR)",
    "edpb_consent_05_2020": "EDPB Guidelines 05/2020 on consent",
    "edpb_breach_09_2022": "EDPB Guidelines 9/2022 on personal data breach notification",
    "edpb_access_01_2022": "EDPB Guidelines 01/2022 on data subject rights: right of access",
}
VERSION_DATES = {
    "gdpr": "2016-05-04",
    "edpb_consent_05_2020": "2020-07-28",
    "edpb_breach_09_2022": "2023-04-06",
    "edpb_access_01_2022": "2023-04-06",
}


def _window_text(text: str, max_tokens: int, token_counter: Callable[[str], int]) -> list[str]:
    words = text.split()
    windows: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and token_counter(candidate) > max_tokens:
            windows.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        windows.append(" ".join(current))
    return windows


def _split_oversized(text: str, max_tokens: int, token_counter: Callable[[str], int]) -> list[str]:
    parts = re.split(r"(?=^\([a-z]\)\s)", text, flags=re.MULTILINE)
    parts = [part.strip() for part in parts if part.strip()]
    point_parts = [part for part in parts if POINT.match(part)]
    if point_parts and all(token_counter(part) <= max_tokens + 2 for part in point_parts):
        lead_in = [part for part in parts if not POINT.match(part)]
        if lead_in:
            point_parts[0] = " ".join([*lead_in, point_parts[0]])
        return point_parts
    result: list[str] = []
    current: list[str] = []
    for part in parts:
        candidate = " ".join([*current, part])
        if current and token_counter(candidate) > max_tokens:
            result.append(" ".join(current))
            current = [part]
        else:
            current.append(part)
    if current:
        result.append(" ".join(current))
    result = [piece for part in result for piece in _window_text(part, max_tokens, token_counter)]
    return result


def _make_chunk(
    unit: dict,
    text: str,
    chunk_id: str,
    citation_label: str,
    breadcrumb: str,
    token_counter: Callable[[str], int],
    locator: str,
    split_index: int | None = None,
) -> Chunk:
    display = text.strip()
    if split_index is not None:
        chunk_id = f"{chunk_id}:part{split_index}"
    return Chunk(
        chunk_id=chunk_id,
        source_id=unit["source_id"],
        doc_type=unit["doc_type"],
        instrument=INSTRUMENTS[unit["source_id"]],
        effective_date="2018-05-25" if unit["source_id"] == "gdpr" else VERSION_DATES[unit["source_id"]],
        version_date=unit.get("version_date", VERSION_DATES[unit["source_id"]]),
        chapter=unit.get("chapter"),
        chapter_title=unit.get("chapter_title"),
        section=unit.get("section"),
        article=unit.get("article"),
        article_title=unit.get("article_title"),
        paragraph=unit.get("paragraph"),
        recital=unit.get("recital"),
        guideline_section=unit.get("guideline_section"),
        citation_label=citation_label,
        breadcrumb=breadcrumb,
        url=(
            f"https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_{unit['article']}"
            if unit.get("article") is not None
            else "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
        ),
        display_text=display,
        embed_text=f"{breadcrumb}\n\n{display}",
        token_count=token_counter(display),
        content_hash=hashlib.sha256(display.encode("utf-8")).hexdigest(),
    )


def build_chunks(
    units: list[dict],
    token_counter: Callable[[str], int],
    max_tokens: int = 450,
    guideline_tokens: int = 400,
    overlap: int = 60,
    token_ids: Callable[[str], list[int]] | None = None,
    decode_ids: Callable[[list[int]], str] | None = None,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for unit in units:
        source = unit["source_id"]
        if source == "gdpr" and unit["doc_type"] == "regulation_article":
            prefix = "GDPR"
            if unit.get("chapter"):
                prefix += f" > Chapter {unit['chapter']}"
            if unit.get("section"):
                prefix += f" > Section {unit['section']}"
            article = unit["article"]
            title = unit.get("article_title", "")
            prefix += f" > Article {article}" + (f" — {title}" if title else "")
            breadcrumb = f"{prefix} > ({unit['paragraph']})"
            label = f"GDPR Art. {article}({unit['paragraph']})"
            chunk_id = f"gdpr:art{article}:p{unit['paragraph']}"
            texts = [unit["text"]]
            if token_counter(unit["text"]) > max_tokens:
                texts = _split_oversized(unit["text"], max_tokens, token_counter)
            for index, text in enumerate(texts, start=1):
                chunks.append(
                    _make_chunk(
                        unit,
                        text,
                        chunk_id,
                        label,
                        breadcrumb,
                        token_counter,
                        "article",
                        index if len(texts) > 1 else None,
                    )
                )
        elif source == "gdpr":
            recital = unit["recital"]
            chunks.append(
                _make_chunk(
                    unit,
                    unit["text"],
                    f"gdpr:rec{recital}",
                    f"GDPR Recital {recital}",
                    f"GDPR > Recital {recital}",
                    token_counter,
                    "recital",
                )
            )
        else:
            section = unit.get("guideline_section") or "0"
            if token_ids is not None and decode_ids is not None:
                ids = token_ids(unit["text"])
                step = max(1, guideline_tokens - overlap)
                texts = [decode_ids(ids[start : start + guideline_tokens]) for start in range(0, len(ids), step)]
                texts = [piece for text in texts for piece in _window_text(text, guideline_tokens, token_counter)]
            else:
                words = unit["text"].split()
                step = max(1, guideline_tokens - overlap)
                texts = [" ".join(words[start : start + guideline_tokens]) for start in range(0, len(words), step)]
            label = (
                f"EDPB 05/2020 §{section}"
                if "consent" in source
                else f"EDPB 9/2022 §{section}"
                if "breach" in source
                else f"EDPB 01/2022 §{section}"
            )
            for index, text in enumerate(texts, start=1):
                chunks.append(
                    _make_chunk(
                        unit,
                        text,
                        f"{source}:s{section}:c{index:02d}",
                        label,
                        f"{INSTRUMENTS[source]} > Section {section} > {unit.get('title', '')}",
                        token_counter,
                        "guideline",
                    )
                )
    merged: dict[str, Chunk] = {}
    for chunk in chunks:
        if chunk.chunk_id in merged:
            existing = merged[chunk.chunk_id]
            existing.display_text += " " + chunk.display_text
            existing.embed_text = f"{existing.breadcrumb}\n\n{existing.display_text}"
            existing.token_count = token_counter(existing.display_text)
            existing.content_hash = hashlib.sha256(existing.display_text.encode("utf-8")).hexdigest()
        else:
            merged[chunk.chunk_id] = chunk
    return list(merged.values())


def main() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    processed_dir = backend_root / "data" / "processed"
    units: list[dict] = []
    for path in sorted(processed_dir.glob("*_units.jsonl")):
        units.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    from app.retrieval.embedder import get_model, token_count

    tokenizer = get_model().tokenizer
    chunks = build_chunks(
        units,
        token_counter=token_count,
        token_ids=lambda text: tokenizer.encode(text, add_special_tokens=False),
        decode_ids=lambda ids: tokenizer.decode(ids, skip_special_tokens=True),
    )
    output = processed_dir / "chunks.jsonl"
    output.write_text(
        "\n".join(chunk.model_dump_json() for chunk in chunks) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(chunks)} chunks to {output}")


if __name__ == "__main__":
    main()
