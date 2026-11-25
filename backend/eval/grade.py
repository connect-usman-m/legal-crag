from pathlib import Path
from typing import Any

import yaml

from app.core.config import Settings
from app.llm.groq_client import get_grader
from app.llm.prompts import GRADER_PROMPT_V1
from app.schemas.eval import EvalItem
from app.schemas.llm import GradeOutput
from eval.answer import answer_correct

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def grade_prompt(item: EvalItem, answer: str, sources: list[dict[str, Any]]) -> str:
    reference_points = "\n".join(f"- {point}" for point in item.reference_points)
    source_text = "\n".join(
        f"[{source.get('id', source.get('label'))}] {source.get('label', '')}: {source.get('snippet', '')}"
        for source in sources
    )
    return GRADER_PROMPT_V1.format(
        question=item.question,
        reference_points=reference_points,
        sources=source_text or "No sources were provided to the generator.",
        answer=answer,
    )


def grade_values(
    item: EvalItem,
    grader,
    abstained: bool,
    acceptable_abstain: bool,
    answer: str = "",
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    output: GradeOutput = grader.invoke(grade_prompt(item, answer, sources or []))
    verdict = output.verdict
    return {
        "grade": verdict,
        "grade_source": "llm",
        "answer_correct": answer_correct(verdict, abstained, acceptable_abstain),
        "unsupported_claims": output.unsupported_claims,
        "rationale": output.rationale,
        "reference_points_met": output.reference_points_met,
    }


def load_overrides(path: Path | None = None) -> list[dict[str, Any]]:
    target = path or BACKEND_ROOT / "eval" / "manual_overrides.yaml"
    if not target.exists():
        return []
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    return data or []


def apply_manual_overrides(
    records: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
    items: list[EvalItem] | None = None,
) -> list[dict[str, Any]]:
    acceptable = {item.qid: item.acceptable_abstain for item in items or []}
    for record in records:
        for override in overrides:
            if override.get("qid") != record["qid"] or override.get("mode") != record["mode"]:
                continue
            grade = override["grade"]
            record["grade"] = grade
            record["grade_source"] = "manual"
            record["answer_correct"] = answer_correct(grade, record["abstained"], acceptable.get(record["qid"], False))
            if "note" in override:
                record["manual_note"] = override["note"]
    return records


async def grade_answer(
    item: EvalItem,
    answer: str,
    sources: list[dict[str, Any]],
    abstained: bool,
    settings: Settings | None = None,
):
    return grade_values(
        item,
        get_grader(settings),
        abstained,
        item.acceptable_abstain,
        answer,
        sources,
    )
