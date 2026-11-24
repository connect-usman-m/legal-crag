import asyncio
from time import perf_counter
from typing import Any

from app.core.config import Settings
from app.graph.decision import decide, decision_reason
from app.graph.state import chunk_field
from app.llm.groq_client import get_judge
from app.llm.judge_cache import cache_key, cached_output, load_cache, save_cache
from app.llm.prompts import EVALUATOR_PROMPT_V1, EVALUATOR_PROMPT_V2, EVALUATOR_PROMPT_V3
from app.schemas.llm import JudgeOutput
from app.schemas.retrieval import ChunkScore

PROMPTS = {
    "V1": EVALUATOR_PROMPT_V1,
    "V2": EVALUATOR_PROMPT_V2,
    "V3": EVALUATOR_PROMPT_V3,
}


def score_from_output(chunk_id: str, output: JudgeOutput | None) -> ChunkScore:
    if output is None:
        return ChunkScore(chunk_id=chunk_id, error=True)
    return ChunkScore(
        chunk_id=chunk_id,
        score=output.score,
        verdict=output.verdict,
        reason=output.reason,
        jurisdiction_match=output.jurisdiction_match,
    )


async def _judge_batch(judge, prompts: list[str], config: Settings) -> list[JudgeOutput | None]:
    batch_config = {"max_concurrency": config.judge_concurrency}
    outputs = await judge.abatch(prompts, config=batch_config, return_exceptions=True)
    if all(isinstance(output, JudgeOutput) for output in outputs):
        return outputs
    await asyncio.sleep(1)
    repaired: list[JudgeOutput | None] = []
    for prompt, output in zip(prompts, outputs):
        if isinstance(output, JudgeOutput):
            repaired.append(output)
            continue
        try:
            repaired.append(await judge.ainvoke(prompt))
        except Exception:
            repaired.append(None)
    return repaired


async def evaluate_chunks(state: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    config = settings or Settings()
    template = PROMPTS[config.evaluator_prompt_version]
    question = state["question"]
    cache = load_cache()
    outputs: list[JudgeOutput | None] = []
    pending: list[tuple[str, str]] = []
    for chunk in state["retrieved"]:
        chunk_id = str(chunk_field(chunk, "chunk_id"))
        cached = cached_output(cache, config.evaluator_prompt_version, question, chunk_id)
        outputs.append(cached)
        if cached is None:
            pending.append(
                (
                    chunk_id,
                    template.format(
                        question=question,
                        label=str(chunk_field(chunk, "citation_label", chunk_id)),
                        text=str(chunk_field(chunk, "display_text", ""))[:1200],
                    ),
                )
            )

    if pending:
        judge = get_judge(config)
        judged = await _judge_batch(judge, [prompt for _, prompt in pending], config)
        for (chunk_id, _), output in zip(pending, judged):
            index = next(i for i, chunk in enumerate(state["retrieved"]) if chunk["chunk_id"] == chunk_id)
            outputs[index] = output
            if output is not None:
                key = cache_key(config.evaluator_prompt_version, question, chunk_id)
                cache[key] = output.model_dump()
        save_cache(cache)

    scores = [
        score_from_output(str(chunk_field(chunk, "chunk_id")), output)
        for chunk, output in zip(state["retrieved"], outputs)
    ]
    return {
        "chunk_scores": scores,
        "retrieval_decision": decide(scores, config.upper_threshold, config.lower_threshold),
        "decision_reason": decision_reason(scores, config.upper_threshold, config.lower_threshold),
        "prompt_versions": {"evaluator": config.evaluator_prompt_version},
    }


async def evaluate(state: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    config = settings or Settings()
    start = perf_counter()
    result = await evaluate_chunks(state, config)
    result.pop("prompt_versions", None)
    result["timings_ms"] = {"evaluate": int((perf_counter() - start) * 1000)}
    return result
