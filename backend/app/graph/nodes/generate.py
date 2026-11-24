import re
from time import perf_counter
from typing import Any

from app.core.config import Settings
from app.llm.prompts import GENERATE_PROMPT_V1
from app.pipelines.naive_rag import get_generator
from app.schemas.retrieval import ContextSource

CITATION = re.compile(r"[\[\u3010]S(\d+)[\]\u3011]")


def render_sources(sources: list[ContextSource]) -> str:
    blocks = []
    for source in sources:
        kind = source.kind
        blocks.append(f"[{source.sid}] ({kind}) {source.label}\n{source.text}")
    return "\n\n".join(blocks)


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
    response = get_generator(config).invoke(prompt)
    answer = re.sub(r"[\u3010]S(\d+)[\u3011]", r"[S\1]", str(response.content)).strip()
    used = [source.sid for source in sources if f"[S{source.sid[1:]}]" in answer]
    return {
        "draft_answer": answer,
        "used_source_ids": used,
        "abstained": answer.startswith("NOT ENOUGH EVIDENCE"),
        "generation_attempts": 1,
        "timings_ms": {"generate": int((perf_counter() - start) * 1000)},
    }
