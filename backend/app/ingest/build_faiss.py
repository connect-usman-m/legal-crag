import json
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np

from app.core.config import Settings
from app.retrieval.embedder import embed_documents


def main() -> None:
    settings = Settings()
    backend_root = Path(__file__).resolve().parents[2]
    chunks = [
        json.loads(line)
        for line in (backend_root / "data" / "processed" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    embeddings = embed_documents([chunk["embed_text"] for chunk in chunks], settings.embed_model)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.asarray(embeddings, dtype=np.float32))
    directory = Path(settings.faiss_dir)
    directory.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(directory / "index.faiss"))
    (directory / "docstore.json").write_text(
        json.dumps(
            {
                "ids": [chunk["chunk_id"] for chunk in chunks],
                "meta": {chunk["chunk_id"]: chunk for chunk in chunks},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (directory / "build.json").write_text(
        json.dumps(
            {
                "corpus_version": settings.chroma_collection,
                "embed_model": settings.embed_model,
                "n_vectors": len(chunks),
                "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        ),
        encoding="utf-8",
    )
    print(f"Built FAISS index with {len(chunks)} vectors")


if __name__ == "__main__":
    main()
