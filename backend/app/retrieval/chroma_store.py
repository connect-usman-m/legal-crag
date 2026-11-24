import json
from functools import lru_cache
from pathlib import Path

import chromadb
import numpy as np

from app.core.config import Settings
from app.retrieval.embedder import embed_query


def configure_collection(client: chromadb.ClientAPI, name: str):
    return client.get_or_create_collection(
        name=name,
        configuration={"hnsw": {"space": "cosine"}},
        metadata={"corpus_version": "gdpr_v1"},
    )


@lru_cache(maxsize=1)
def get_collection(persist_dir: str | None = None, collection_name: str | None = None):
    settings = Settings()
    client = chromadb.PersistentClient(path=persist_dir or settings.chroma_dir)
    return configure_collection(client, collection_name or settings.chroma_collection)


def query_vectors(collection, vector: list[float] | np.ndarray, k: int) -> list[list[float]]:
    result = collection.query(query_embeddings=[np.asarray(vector, dtype=np.float32).tolist()], n_results=k)
    return result["distances"]


def similarity_search(question: str, k: int | None = None):
    settings = Settings()
    collection = get_collection(settings.chroma_dir, settings.chroma_collection)
    result = collection.query(
        query_embeddings=[embed_query(question, settings.embed_model).tolist()],
        n_results=k or settings.retrieve_k,
        include=["documents", "metadatas", "distances"],
    )
    ids = result["ids"][0]
    distances = result["distances"][0]
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    return [
        {
            "chunk_id": chunk_id,
            "display_text": document,
            "metadata": metadata,
            "similarity": 1 - float(distance),
        }
        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances)
    ]


def load_chunks(path: str | Path) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]
