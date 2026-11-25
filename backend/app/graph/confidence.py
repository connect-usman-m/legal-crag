from app.schemas.retrieval import ContextSource

SOURCE_FACTORS = {
    "CORRECT": 1.0,
    "AMBIGUOUS": 0.85,
    "INCORRECT": 0.7,
    None: 1.0,
}


def compute_confidence(
    cited_sources: list[ContextSource],
    decision: str | None,
    coverage: float,
    abstained: bool,
    low_coverage: bool = False,
) -> tuple[float, str]:
    if abstained:
        return 0.0, "None"
    if not cited_sources:
        return 0.0, "Low"
    evidence = sum(source.relevance for source in cited_sources) / len(cited_sources)
    value = evidence * coverage * SOURCE_FACTORS.get(decision, 1.0)
    if low_coverage:
        value *= 0.5
    value = round(value, 2)
    label = "High" if value >= 0.7 else "Medium" if value >= 0.45 else "Low"
    return value, label
