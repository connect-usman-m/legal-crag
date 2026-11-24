import json

import faiss
import numpy as np

from app.core.config import Settings
from app.ingest.manifest import build_manifest, validate_stores


def test_manifest_counts_sources_and_records_embed_model():
    manifest = build_manifest(
        sqlite=object(),
        source_files=[
            ("gdpr", "raw/gdpr.pdf", "abc"),
            ("edpb_consent_05_2020", "raw/consent.pdf", "def"),
        ],
        chunks=[{"chunk_id": "gdpr:art1:p1"}, {"chunk_id": "gdpr:rec1"}],
        token_count=120,
        embed_model="BAAI/bge-small-en-v1.5",
        embed_dim=384,
    )

    assert manifest["totals"] == {"chunks": 2, "tokens": 120}
    assert manifest["sources"][0]["sha256"] == "abc"
    assert manifest["embed_model"] == "BAAI/bge-small-en-v1.5"
    assert manifest["stores"]["faiss_index"] == "data/faiss/index.faiss"


def test_validate_stores_rejects_index_mismatch(tmp_path):
    settings = Settings(_env_file=None, groq_api_key="x", tavily_api_key="x")
    index = faiss.IndexFlatIP(384)
    index.add(np.zeros((3, 384), dtype=np.float32))
    faiss.write_index(index, str(tmp_path / "index.faiss"))
    (tmp_path / "docstore.json").write_text(json.dumps({"ids": ["a", "b", "c"], "meta": {}}))

    manifest = {"totals": {"chunks": 4}}

    assert validate_stores(settings, manifest, faiss_dir=str(tmp_path), chroma_count=3) is False
