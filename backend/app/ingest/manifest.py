import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import Settings

SOURCE_IDS = {
    "gdpr.pdf": "gdpr",
    "gdpr.html": "gdpr",
    "edpb_consent_05_2020.pdf": "edpb_consent_05_2020",
    "edpb_breach_09_2022.pdf": "edpb_breach_09_2022",
    "edpb_access_01_2022.pdf": "edpb_access_01_2022",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_manifest(
    source_files: list[tuple[str, str, str]],
    chunks: list[dict],
    token_count: int,
    embed_model: str,
    embed_dim: int,
    **_: object,
) -> dict:
    by_source: dict[str, dict] = {}
    for source_id, path, checksum in source_files:
        by_source.setdefault(
            source_id,
            {
                "source_id": source_id,
                "url": path,
                "sha256": checksum,
                "units": 0,
                "chunks": 0,
            },
        )
    for chunk in chunks:
        source_id = chunk.get("source_id", "gdpr")
        entry = by_source.setdefault(
            source_id,
            {"source_id": source_id, "url": "", "sha256": "", "units": 0, "chunks": 0},
        )
        entry["chunks"] += 1
    return {
        "corpus_version": "gdpr_v1",
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "embed_model": embed_model,
        "embed_dim": embed_dim,
        "chunker_version": "1.0.0",
        "sources": list(by_source.values()),
        "totals": {"chunks": len(chunks), "tokens": token_count},
        "stores": {
            "chroma_collection": "gdpr_v1",
            "faiss_index": "data/faiss/index.faiss",
        },
    }


def validate_stores(
    settings: Settings,
    manifest: dict,
    faiss_dir: str | None = None,
    chroma_count: int | None = None,
) -> bool:
    directory = Path(faiss_dir or settings.faiss_dir)
    docstore = json.loads((directory / "docstore.json").read_text(encoding="utf-8"))
    n_vectors = len(docstore["ids"])
    if chroma_count is None:
        import chromadb

        client = chromadb.PersistentClient(path=settings.chroma_dir)
        chroma_count = client.get_collection(settings.chroma_collection).count()
    return n_vectors == chroma_count == manifest["totals"]["chunks"]


def main() -> None:
    settings = Settings()
    backend_root = Path(__file__).resolve().parents[2]
    raw_dir = backend_root / "data" / "raw"
    source_files = [
        (SOURCE_IDS[path.name], str(path.relative_to(backend_root)), sha256_file(path))
        for path in sorted(raw_dir.iterdir())
        if path.name in SOURCE_IDS
    ]
    chunks = [
        json.loads(line)
        for line in (backend_root / "data" / "processed" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    manifest = build_manifest(
        source_files=source_files,
        chunks=chunks,
        token_count=sum(chunk["token_count"] for chunk in chunks),
        embed_model=settings.embed_model,
        embed_dim=384,
    )
    output = backend_root / "data" / "manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manifest with {manifest['totals']['chunks']} chunks to {output}")


if __name__ == "__main__":
    main()
