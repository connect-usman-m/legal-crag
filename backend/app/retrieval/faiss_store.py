import json
from functools import lru_cache
from pathlib import Path

import faiss

from app.core.config import Settings
from app.retrieval.embedder import embed_query


@lru_cache(maxsize=1)
def get_index(faiss_dir: str | None = None):
    settings = Settings()
    directory = Path(faiss_dir or settings.faiss_dir)
    index = faiss.read_index(str(directory / "index.faiss"))
    docstore = json.loads((directory / "docstore.json").read_text(encoding="utf-8"))
    return index, docstore


def similarity_search(question: str, k: int | None = None):
    settings = Settings()
    index, docstore = get_index(settings.faiss_dir)
    vector = embed_query(question, settings.embed_model).reshape(1, -1)
    scores, rows = index.search(vector, k or settings.naive_k)
    results = []
    for score, row in zip(scores[0], rows[0]):
        if row < 0:
            continue
        chunk_id = docstore["ids"][row]
        results.append(
            {
                "chunk_id": chunk_id,
                "display_text": docstore["meta"][chunk_id]["display_text"],
                "metadata": docstore["meta"][chunk_id],
                "similarity": float(score),
            }
        )
    return results
