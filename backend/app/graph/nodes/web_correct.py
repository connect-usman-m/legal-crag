import hashlib
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from tavily import TavilyClient

from app.core.config import Settings
from app.llm.groq_client import get_rewriter
from app.llm.prompts import REWRITE_PROMPT_V1
from app.retrieval.reranker import rerank_web_results
from app.schemas.retrieval import ContextSource, WebResult


async def rewrite_query(question: str, settings: Settings | None = None) -> str:
    config = settings or Settings()
    rewriter = get_rewriter(config)
    prompt = REWRITE_PROMPT_V1.format(question=question)
    try:
        output = await rewriter.ainvoke(prompt)
        return output.query.strip() or question
    except Exception:
        return question


def search_web(
    query: str,
    settings: Settings | None = None,
    base_url: str | None = None,
) -> list[WebResult]:
    config = settings or Settings()
    client = TavilyClient(api_key=config.tavily_api_key, api_base_url=base_url)
    options: dict[str, Any] = {
        "search_depth": "advanced",
        "max_results": 6,
        "include_raw_content": False,
        "include_answer": False,
        "timeout": 8,
    }
    if config.web_domain_allowlist:
        options["include_domains"] = config.web_domain_allowlist
    response = client.search(query, **options)
    results = []
    for hit in response.get("results", []):
        url = hit["url"]
        results.append(
            WebResult(
                result_id="web:" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:10],
                url=url,
                domain=urlparse(url).hostname or "",
                title=hit.get("title", ""),
                content=hit.get("content", ""),
                tavily_score=hit.get("score"),
                retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
        )
    return rerank_web_results(query, results, config.rerank_model)


def web_sources(results: list[WebResult], limit: int) -> list[ContextSource]:
    return [
        ContextSource(
            sid=f"S{index}",
            kind="web",
            ref_id=result.result_id,
            label=result.domain,
            title=result.title,
            url=result.url,
            text=result.content,
            relevance=result.final_score,
        )
        for index, result in enumerate(results[:limit], start=1)
    ]


async def web_correct(
    state: dict[str, Any],
    settings: Settings | None = None,
    web_top_n: int | None = None,
) -> dict[str, Any]:
    config = settings or Settings()
    query = await rewrite_query(state["question"], config)
    try:
        results = search_web(query, config)
    except Exception:
        return {
            "web_query": query,
            "web_results": [],
            "context_sources": [],
            "warnings": ["web_search_failed"],
        }
    top = results[: web_top_n or config.web_top_n]
    for score in state.get("chunk_scores", []):
        score.kept = False
    return {
        "web_query": query,
        "web_results": top,
        "context_sources": web_sources(top, len(top)),
        "chunk_scores": state.get("chunk_scores", []),
        "warnings": [],
    }
