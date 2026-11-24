from typing import Literal

from pydantic import BaseModel, Field


class EvalItem(BaseModel):
    qid: str
    split: Literal["dev", "test"]
    category: Literal["covered", "not_covered", "ambiguous"]
    question: str
    expected_branch: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]
    reference_points: list[str] = Field(default_factory=list)
    expected_corpus_refs: list[str] = Field(default_factory=list)
    acceptable_abstain: bool = False
    notes: str | None = None
