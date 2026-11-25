import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_runtime, get_settings, require_demo_key
from app.schemas.api import CorpusStats, HealthResponse

router = APIRouter(tags=["meta"])
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def groq_models_available(settings) -> bool:
    from groq import Groq

    try:
        client = Groq(api_key=settings.groq_api_key)
        available = {model.id for model in client.models.list().data}
    except Exception:
        return False
    return settings.groq_judge_model in available and settings.groq_gen_model in available


@router.get("/health", response_model=HealthResponse)
async def health(settings=Depends(get_settings), runtime=Depends(get_runtime)):
    checks = {
        "chroma": Path(settings.chroma_dir).exists(),
        "faiss": Path(settings.faiss_dir, "index.faiss").exists(),
        "embedder": runtime.embedder is not None,
        "reranker": runtime.reranker is not None,
        "graph": runtime.graph is not None,
        "groq_models": groq_models_available(settings),
        "tavily_key": bool(settings.tavily_api_key),
        "langsmith": bool(settings.langsmith_api_key) if settings.langsmith_tracing else True,
    }
    ready = all(value for name, value in checks.items() if name != "langsmith")
    return HealthResponse(
        status="ok" if ready else "degraded",
        ready=ready,
        checks=checks,
        corpus_version=settings.chroma_collection,
    )


@router.get("/corpus/stats", response_model=CorpusStats, dependencies=[Depends(require_demo_key)])
async def corpus_stats():
    path = BACKEND_ROOT / "data" / "manifest.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Index not ready")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return CorpusStats(
        corpus_version=manifest["corpus_version"],
        built_at=manifest["built_at"],
        totals=manifest["totals"],
        by_source=manifest["sources"],
    )


@router.get("/eval/results", dependencies=[Depends(require_demo_key)])
async def eval_results():
    candidates = sorted((BACKEND_ROOT / "eval" / "results").glob("**/results.json"))
    if not candidates:
        raise HTTPException(status_code=404, detail="No evaluation results found")
    return json.loads(candidates[-1].read_text(encoding="utf-8"))
