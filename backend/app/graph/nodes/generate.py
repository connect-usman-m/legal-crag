from time import perf_counter
from typing import Any

from app.core.config import Settings
from app.llm.groq_client import get_generator
from app.llm.prompts import GENERATE_PROMPT_V1
from app.schemas.retrieval import ContextSource


def render_sources(sources: list[ContextSource]) -> str:
    return "\n\n".join(f"[{source.sid}] ({source.kind}) {source.label}\n{source.text}" for source in sources)


async def generate(state: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    config = settings or Settings()
    start = perf_counter()
    sources = state.get("context_sources", [])
    if not sources:
        return {
            "draft_answer": "NOT ENOUGH EVIDENCE: no sources were available",
            "used_source_ids": [],
            "abstained": True,
            "generation_attempts": 0,
            "timings_ms": {"generate": int((perf_counter() - start) * 1000)},
        }
    prompt = GENERATE_PROMPT_V1.format(question=state["question"], context=render_sources(sources))
    output = get_generator(config).invoke(prompt)
    return {
        "draft_answer": output.answer,
        "used_source_ids": output.used_source_ids,
        "abstained": output.abstained,
        "generation_attempts": 1,
        "timings_ms": {"generate": int((perf_counter() - start) * 1000)},
    }
