import asyncio
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from langsmith.run_helpers import LangSmithExtra

from app.api.deps import Runtime, require_demo_key
from app.core.config import Settings
from app.core.tracing import traced_query
from app.graph.nodes.cite import cite
from app.graph.nodes.generate import generate
from app.retrieval import faiss_store
from app.schemas.api import (
    ChunkScoreOut,
    CompareRequest,
    CompareResponse,
    QueryRequest,
    QueryResponse,
    SourceOut,
)

router = APIRouter(prefix="/query", tags=["query"])


def _sources(state: dict[str, Any], abstained: bool) -> list[SourceOut]:
    return [
        SourceOut(
            id=source.sid,
            type=source.kind,
            label=source.label,
            title=source.title,
            url=source.url,
            snippet=source.text[:600],
            relevance_score=source.relevance,
            used=not abstained,
        )
        for source in state.get("sources", [])
    ]


def _to_response(state: dict[str, Any], request: QueryRequest, settings: Settings, latency_ms: int) -> QueryResponse:
    labels = {}
    for chunk in state.get("retrieved", []):
        chunk_id = chunk.chunk_id if hasattr(chunk, "chunk_id") else chunk["chunk_id"]
        label = chunk.citation_label if hasattr(chunk, "citation_label") else chunk.get("citation_label", chunk_id)
        labels[chunk_id] = label
    return QueryResponse(
        request_id=state["request_id"],
        mode=request.mode,
        question=state["question"],
        answer=state.get("answer", ""),
        abstained=state.get("abstained", False),
        sources=_sources(state, state.get("abstained", False)),
        retrieval_decision=state.get("retrieval_decision"),
        decision_reason=state.get("decision_reason"),
        confidence=state.get("confidence", 0.0),
        confidence_label=state.get("confidence_label", "Low"),
        citation_coverage=state.get("citation_report", {}).get("coverage", 0.0),
        warnings=state.get("warnings", []),
        web_query=state.get("web_query"),
        chunk_scores=[
            ChunkScoreOut.model_validate(
                {
                    **(score.model_dump() if hasattr(score, "model_dump") else score),
                    "label": labels.get(
                        score.chunk_id if hasattr(score, "chunk_id") else score["chunk_id"],
                        score.chunk_id if hasattr(score, "chunk_id") else score["chunk_id"],
                    ),
                }
            )
            for score in state.get("chunk_scores", [])
        ]
        if request.mode == "crag"
        else None,
        trace_id=state.get("trace_id"),
        trace_url=state.get("trace_url"),
        latency_ms=latency_ms,
        timings_ms={"total": latency_ms} if request.debug else None,
        models={
            "judge": settings.groq_judge_model,
            "generator": settings.groq_gen_model,
            "embed": settings.embed_model,
            "rerank": settings.rerank_model,
        },
        prompt_versions={"evaluator": settings.evaluator_prompt_version, "generate": "V1"},
        thresholds={
            "upper": settings.upper_threshold,
            "lower": settings.lower_threshold,
            "keep": settings.keep_threshold,
        }
        if request.mode == "crag"
        else None,
    )


async def run_crag_query(state: dict[str, Any], settings: Settings, runtime: Runtime) -> dict[str, Any]:
    result = await runtime.graph.ainvoke(
        state,
        config={
            "run_name": "crag_graph",
            "tags": ["mode:crag"],
            "metadata": {"request_id": state["request_id"], "mode": "crag"},
        },
    )
    return result


async def run_naive_query(state: dict[str, Any], settings: Settings, runtime: Runtime) -> dict[str, Any]:
    results = faiss_store.similarity_search(state["question"], k=runtime.settings.naive_k)
    sources = [
        {
            "sid": f"S{index}",
            "kind": "corpus",
            "ref_id": result["chunk_id"],
            "label": result["metadata"].get("citation_label", result["chunk_id"]),
            "url": result["metadata"].get("url", ""),
            "text": result["display_text"],
            "relevance": result["similarity"],
        }
        for index, result in enumerate(results, start=1)
    ]
    from app.schemas.retrieval import ContextSource

    context = [ContextSource.model_validate(source) for source in sources]
    draft = await generate({**state, "context_sources": context}, runtime.settings)
    cited = await cite({**state, **draft, "context_sources": context}, runtime.settings)
    return {**state, **draft, **cited, "warnings": draft.get("warnings", []) + cited.get("warnings", [])}


async def _run(payload: dict[str, Any], settings: Settings, runtime: Runtime) -> dict[str, Any]:
    request = QueryRequest.model_validate(payload["request"])
    state = {
        "request_id": payload["request_id"],
        "question": request.question,
        "mode": request.mode,
        "warnings": [],
        "timings_ms": {},
    }
    if request.mode == "crag":
        return await run_crag_query(state, settings, runtime)
    return await run_naive_query(state, settings, runtime)


@router.post("", response_model=QueryResponse, dependencies=[Depends(require_demo_key)])
async def query(request: QueryRequest, http_request: Request):
    settings = http_request.app.state.settings
    runtime = http_request.app.state.runtime
    request_id = str(uuid4())
    start = perf_counter()
    try:
        state = await asyncio.wait_for(
            traced_query(
                {"request": request.model_dump(), "request_id": request_id, "mode": request.mode},
                lambda: _run(
                    {"request": request.model_dump(), "request_id": request_id, "mode": request.mode},
                    settings,
                    runtime,
                ),
                settings,
                langsmith_extra=LangSmithExtra(project_name=settings.langsmith_project),
            ),
            timeout=30,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request exceeded 30 seconds") from None
    latency_ms = int((perf_counter() - start) * 1000)
    state = {"question": request.question, "request_id": request_id, "mode": request.mode, **state}
    return _to_response(state, request, settings, latency_ms)


compare_router = APIRouter(tags=["compare"])


@compare_router.post("/compare", response_model=CompareResponse, dependencies=[Depends(require_demo_key)])
async def compare(request: CompareRequest, http_request: Request):
    settings = http_request.app.state.settings
    runtime = http_request.app.state.runtime
    query_request = QueryRequest(question=request.question)

    async def one(mode: str):
        payload = {
            "request": {**query_request.model_dump(), "mode": mode},
            "request_id": str(uuid4()),
            "mode": mode,
        }
        start = perf_counter()
        state = await traced_query(
            payload,
            lambda: _run(payload, settings, runtime),
            settings,
            langsmith_extra=LangSmithExtra(project_name=settings.langsmith_project),
        )
        merged = {"question": request.question, "request_id": payload["request_id"], "mode": mode, **state}
        return _to_response(merged, query_request, settings, int((perf_counter() - start) * 1000))

    naive, crag = await asyncio.gather(one("naive"), one("crag"))
    return CompareResponse(naive=naive, crag=crag)
