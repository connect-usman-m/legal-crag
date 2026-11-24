import json
from pathlib import Path

from app.core.config import Settings
from app.retrieval.chroma_store import configure_collection
from app.retrieval.embedder import embed_documents


def main() -> None:
    import chromadb

    settings = Settings()
    backend_root = Path(__file__).resolve().parents[2]
    chunks = [
        json.loads(line)
        for line in (backend_root / "data" / "processed" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    try:
        client.delete_collection(settings.chroma_collection)
    except Exception as exc:
        if "does not exist" not in str(exc):
            raise
    collection = configure_collection(client, settings.chroma_collection)
    embeddings = embed_documents([chunk["embed_text"] for chunk in chunks], settings.embed_model)
    metadatas = []
    for chunk in chunks:
        metadatas.append(
            {
                "source_id": chunk["source_id"],
                "doc_type": chunk["doc_type"],
                "instrument": chunk["instrument"],
                "jurisdiction": chunk["jurisdiction"],
                "effective_date": chunk["effective_date"],
                "chapter": chunk["chapter"] or "",
                "section": chunk["section"] or "",
                "article": chunk["article"] or 0,
                "paragraph": chunk["paragraph"] or 0,
                "citation_label": chunk["citation_label"],
                "url": chunk["url"],
                "display_text": chunk["display_text"],
                "token_count": chunk["token_count"],
            }
        )
    collection.add(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=[chunk["embed_text"] for chunk in chunks],
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )
    print(f"Built Chroma collection {settings.chroma_collection} with {collection.count()} chunks")


if __name__ == "__main__":
    main()
