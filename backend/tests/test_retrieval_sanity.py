import pytest

from app.retrieval import chroma_store, faiss_store

QUERIES = [
    ("without undue delay where feasible not later than 72 hours supervisory authority", "gdpr:art33"),
    ("processing shall be lawful only if at least one of the following applies consent contract", "gdpr:art6"),
    ("designate a data protection officer public authority large scale regular systematic monitoring", "gdpr:art37"),
    ("administrative fines up to 20 000 000 EUR or 4% total worldwide annual turnover", "gdpr:art83"),
    ("respond to a request without undue delay and in any event within one month", "gdpr:art12"),
    ("freely given specific informed unambiguous indication of the data subject's wishes consent", "gdpr:art4"),
    ("right not to be subject to a decision based solely on automated processing", "gdpr:art22"),
    ("data protection impact assessment shall be carried out prior to the processing", "gdpr:art35"),
    ("transfer of personal data to a third country shall be subject to appropriate safeguards", "gdpr:art44"),
    ("erase personal data without undue delay grounds for erasure right to be forgotten", "gdpr:art17"),
]


@pytest.mark.slow
@pytest.mark.parametrize("store", [chroma_store, faiss_store])
def test_recall_at_five(store):
    found = 0
    for question, expected in QUERIES:
        results = store.similarity_search(question, k=5)
        if any(result["chunk_id"].startswith(expected + ":") for result in results):
            found += 1
    assert found / len(QUERIES) >= 0.8
