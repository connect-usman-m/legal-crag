from typing import Literal

from pydantic import BaseModel, Field


class JudgeOutput(BaseModel):
    score: float = Field(..., ge=0, le=1)
    verdict: Literal["relevant", "partial", "irrelevant"]
    reason: str = Field(..., max_length=240)
    jurisdiction_match: bool


class RewriteOutput(BaseModel):
    query: str = Field(..., max_length=200)


class GenerateOutput(BaseModel):
    answer: str
    used_source_ids: list[str]
    abstained: bool


class GradeOutput(BaseModel):
    verdict: Literal["correct", "partial", "incorrect", "abstained"]
    unsupported_claims: int
    rationale: str
