from time import perf_counter
from typing import Any

from app.core.config import Settings
from app.retrieval import chroma_store
from app.schemas.retrieval import RetrievedChunk


async def retrieve(state: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    config = settings or Settings()
    start = perf_counter()
    results = chroma_store.similarity_search(state["question"], k=config.retrieve_k)
    chunks = [
        RetrievedChunk(
            chunk_id=result["chunk_id"],
            citation_label=result["metadata"].get("citation_label", result["chunk_id"]),
            url=result["metadata"].get("url", ""),
            display_text=result["metadata"].get("display_text", result["display_text"]),
            source_id=result["metadata"].get("source_id", ""),
            doc_type=result["metadata"].get("doc_type", ""),
            similarity=result["similarity"],
        )
        for result in results
    ]
    return {
        "retrieved": chunks,
        "timings_ms": {"retrieve": int((perf_counter() - start) * 1000)},
    }
