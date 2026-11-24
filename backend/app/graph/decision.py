from typing import Literal

from app.schemas.retrieval import ChunkScore

Decision = Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]


def decide(
    scores: list[ChunkScore],
    upper: float = 0.7,
    lower: float = 0.3,
) -> Decision:
    valid = [score.score for score in scores if score.score is not None]
    if not valid:
        return "AMBIGUOUS"
    if max(valid) >= upper:
        return "CORRECT"
    if max(valid) < lower:
        return "INCORRECT"
    return "AMBIGUOUS"


def select_kept(scores: list[ChunkScore], keep: float = 0.5) -> list[ChunkScore]:
    kept = []
    for score in scores:
        score.kept = score.score is not None and score.score >= keep
        if score.kept:
            kept.append(score)
    return kept


def decision_reason(scores: list[ChunkScore], upper: float = 0.7, lower: float = 0.3) -> str:
    valid = [(score.score, score.chunk_id) for score in scores if score.score is not None]
    if not valid:
        return "no scored chunks; conservative AMBIGUOUS"
    best_score, best_id = max(valid)
    return (
        f"max={best_score:.2f} ({best_id}); "
        f"{sum(score >= upper for score, _ in valid)} chunks >= {upper}; "
        f"{sum(score >= lower for score, _ in valid)} chunks >= {lower}"
    )
