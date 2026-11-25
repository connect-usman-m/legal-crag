import re
from typing import Any

from app.core.config import Settings
from app.graph.confidence import compute_confidence
from app.llm.groq_client import get_generator
from app.llm.prompts import GENERATE_PROMPT_V1
from app.schemas.retrieval import ContextSource

CITATION = re.compile(r"[\[\u3010]S(\d+)[\]\u3011]")
EXCLUDED_PREFIXES = ("Not legal advice", "NOT ENOUGH EVIDENCE", "#", "- ", "* ")
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def normalize_answer(answer: str) -> str:
    return re.sub(r"[\u3010]S(\d+)[\u3011]", r"[S\1]", answer)


def factual_sentences(answer: str) -> list[str]:
    sentences = []
    for sentence in SENTENCE.split(answer.strip()):
        sentence = sentence.strip()
        if not sentence or sentence.startswith(EXCLUDED_PREFIXES) or "legal advice" in sentence.lower():
            continue
        sentences.append(sentence)
    return sentences


def citation_report(answer: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    text = normalize_answer(answer)
    valid_ids = {source["sid"] for source in sources}
    cited = [f"S{number}" for number in CITATION.findall(text)]
    valid_cited = [sid for sid in cited if sid in valid_ids]
    invalid_ids = [sid for sid in cited if sid not in valid_ids]
    unused_ids = [sid for sid in valid_ids if sid not in cited]
    sentences = factual_sentences(text)
    cited_sentences = sum(
        any(f"S{number}" in valid_ids for number in CITATION.findall(sentence)) for sentence in sentences
    )
    coverage = cited_sentences / len(sentences) if sentences else 1.0
    return {
        "valid_ids": list(dict.fromkeys(valid_cited)),
        "invalid_ids": list(dict.fromkeys(invalid_ids)),
        "unused_ids": unused_ids,
        "factual_sentences": len(sentences),
        "cited_sentences": cited_sentences,
        "coverage": round(coverage, 6),
    }


def renumber_answer(answer: str, ordered_ids: list[str]) -> str:
    mapping = {old.removeprefix("S"): str(index) for index, old in enumerate(ordered_ids, start=1)}
    return CITATION.sub(lambda match: f"[S{mapping.get(match.group(1), match.group(1))}]", answer)


def render_sources(sources: list[ContextSource]) -> str:
    return "\n\n".join(f"[{source.sid}] ({source.kind}) {source.label}\n{source.text}" for source in sources)


async def regenerate(state: dict[str, Any], settings: Settings) -> str:
    prompt = GENERATE_PROMPT_V1.format(question=state["question"], context=render_sources(state["context_sources"]))
    prompt += "\n\nCorrective instruction: every factual sentence must end with a valid [S#] marker from the context."
    output = get_generator(settings).invoke(prompt)
    return normalize_answer(output.answer.strip())


async def cite(state: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    config = settings or Settings()
    answer = normalize_answer(state["draft_answer"])
    report = citation_report(answer, [source.model_dump() for source in state["context_sources"]])
    warnings: list[str] = []
    low_coverage = False

    if report["invalid_ids"] or report["coverage"] < 0.8:
        answer = await regenerate(state, config)
        report = citation_report(answer, [source.model_dump() for source in state["context_sources"]])
        if report["invalid_ids"] or report["coverage"] < 0.8:
            warnings.append("low_citation_coverage")
            low_coverage = True

    by_sid = {source.sid: source for source in state["context_sources"]}
    ordered_ids = list(dict.fromkeys([f"S{number}" for number in CITATION.findall(answer)]))
    ordered_ids = [sid for sid in ordered_ids if sid in by_sid]
    answer = renumber_answer(answer, ordered_ids)
    sources = []
    for index, sid in enumerate(ordered_ids, start=1):
        source = by_sid[sid].model_copy(update={"sid": f"S{index}"})
        sources.append(source)
    answer = renumber_answer(answer, ordered_ids)

    abstained = answer.startswith("NOT ENOUGH EVIDENCE")
    confidence, label = compute_confidence(
        sources,
        state.get("retrieval_decision"),
        report["coverage"],
        abstained,
        low_coverage,
    )
    return {
        "answer": answer,
        "sources": sources,
        "citation_report": report,
        "confidence": confidence,
        "confidence_label": label,
        "warnings": warnings,
    }
