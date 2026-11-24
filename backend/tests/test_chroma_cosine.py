import math

import chromadb

from app.retrieval.chroma_store import configure_collection, query_vectors


def test_chroma_is_configured_for_cosine_distance(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = configure_collection(client, "cosine-test")

    config = client.get_collection("cosine-test").configuration_json
    assert config["hnsw"]["space"] == "cosine"

    collection.add(
        ids=["a", "b", "c"],
        embeddings=[[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
    )

    distances = query_vectors(collection, [1.0, 0.0], 3)[0]
    assert len(distances) == 3
    assert math.isclose(min(distances), 0.0, abs_tol=0.01)
    assert math.isclose(max(distances), 1.0, abs_tol=0.01)
