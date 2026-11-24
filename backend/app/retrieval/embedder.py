from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import Settings

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def get_model(model_name: str | None = None) -> SentenceTransformer:
    name = model_name or Settings().embed_model
    return SentenceTransformer(name)


def token_count(text: str) -> int:
    tokenizer = get_model().tokenizer
    return len(tokenizer.encode(text, add_special_tokens=False))


def embed_documents(texts: list[str], model_name: str | None = None) -> np.ndarray:
    model = get_model(model_name)
    vectors = model.encode(
        texts,
        batch_size=64,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype=np.float32)


def embed_query(text: str, model_name: str | None = None) -> np.ndarray:
    return embed_documents([QUERY_PREFIX + text], model_name)[0]
