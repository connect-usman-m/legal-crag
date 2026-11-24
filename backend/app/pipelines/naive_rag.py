import re
from typing import Any

from langchain_groq import ChatGroq
from pydantic import SecretStr

from app.core.config import Settings
from app.llm.prompts import GENERATE_PROMPT_V1
from app.retrieval import faiss_store

CITATION = re.compile(r"[\[\u3010]S(\d+)[\]\u3011]")


def render_context(results: list[dict[str, Any]]) -> str:
    blocks = []
    for index, result in enumerate(results, start=1):
        label = result["metadata"].get("citation_label", result["chunk_id"])
        blocks.append(f"[S{index}] (corpus) {label}\n{result['display_text']}")
    return "\n\n".join(blocks)


def parse_citations(answer: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    used = {int(number) for number in CITATION.findall(answer)}
    return [result for index, result in enumerate(results, start=1) if index in used]


def get_generator(settings: Settings | None = None) -> ChatGroq:
    config = settings or Settings()
    return ChatGroq(
        model=config.groq_gen_model,
        temperature=0,
        api_key=SecretStr(config.groq_api_key),
        timeout=20,
        max_retries=2,
    )


def answer_question(question: str, settings: Settings | None = None) -> dict[str, Any]:
    config = settings or Settings()
    results = faiss_store.similarity_search(question, k=config.naive_k)
    prompt = GENERATE_PROMPT_V1.format(question=question, context=render_context(results))
    response = get_generator(config).invoke(prompt)
    answer = re.sub(r"[\u3010]S(\d+)[\u3011]", r"[S\1]", str(response.content)).strip()
    cited = parse_citations(answer, results)
    abstained = answer.startswith("NOT ENOUGH EVIDENCE")
    return {
        "answer": answer,
        "abstained": abstained,
        "sources": cited,
        "retrieval_decision": None,
        "mode": "naive",
    }
