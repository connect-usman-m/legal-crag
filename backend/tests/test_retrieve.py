import pytest

from app.graph.nodes.retrieve import retrieve
from app.schemas.retrieval import RetrievedChunk


@pytest.mark.asyncio
async def test_retrieve_maps_chroma_results_to_chunks(monkeypatch):
    monkeypatch.setattr(
        "app.graph.nodes.retrieve.chroma_store.similarity_search",
        lambda _question, k=None: [
            {
                "chunk_id": "gdpr:art33:p1",
                "display_text": "embed text",
                "similarity": 0.9,
                "metadata": {
                    "citation_label": "GDPR Art. 33(1)",
                    "display_text": "72 hours",
                    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_33",
                    "source_id": "gdpr",
                    "doc_type": "regulation_article",
                },
            }
        ],
    )

    result = await retrieve({"question": "What is the deadline?"})

    chunk = result["retrieved"][0]
    assert isinstance(chunk, RetrievedChunk)
    assert chunk.display_text == "72 hours"
    assert chunk.citation_label == "GDPR Art. 33(1)"
    assert "retrieve" in result["timings_ms"]
