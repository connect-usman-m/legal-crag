import math
from functools import lru_cache
from urllib.parse import urlparse

from sentence_transformers import CrossEncoder

from app.core.config import Settings
from app.schemas.retrieval import WebResult

OFFICIAL_DOMAINS = {"eur-lex.europa.eu", "edpb.europa.eu", "oag.ca.gov", "ico.org.uk", "curia.europa.eu", "hhs.gov"}
REPUTABLE_DOMAINS = {"gdpr-info.eu", "iapp.org"}


def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def domain_trust(url: str) -> float:
    host = host_of(url)
    if not host:
        return 0.3
    if any(host == domain or host.endswith("." + domain) for domain in OFFICIAL_DOMAINS):
        return 1.0
    if host.endswith(".gov"):
        return 1.0
    if any(host == domain or host.endswith("." + domain) for domain in REPUTABLE_DOMAINS):
        return 0.6
    if host.endswith(".law") or ".law." in host:
        return 0.6
    return 0.3


@lru_cache(maxsize=1)
def get_cross_encoder(model_name: str | None = None) -> CrossEncoder:
    return CrossEncoder(model_name or Settings().rerank_model)


def rerank_web_results(
    question: str,
    results: list[WebResult],
    model: str | None = None,
) -> list[WebResult]:
    if not results:
        return []
    encoder = get_cross_encoder(model)
    scores = encoder.predict([(question, f"{result.title} {result.content}") for result in results])
    for result, raw_score in zip(results, scores):
        probability = 1 / (1 + math.exp(-float(raw_score)))
        result.rerank_score = probability
        result.domain_trust = domain_trust(result.url)
        result.final_score = round(0.8 * probability + 0.2 * result.domain_trust, 4)
    return sorted(results, key=lambda result: result.final_score, reverse=True)
