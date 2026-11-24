from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(PROJECT_ENV_FILE), extra="ignore")

    groq_api_key: str
    tavily_api_key: str

    groq_judge_model: str = "openai/gpt-oss-20b"
    groq_gen_model: str = "openai/gpt-oss-120b"
    groq_judge_reasoning_effort: Literal["low", "medium", "high"] = "low"

    embed_model: str = "BAAI/bge-small-en-v1.5"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    chroma_dir: str = "./data/chroma"
    chroma_collection: str = "gdpr_v1"
    faiss_dir: str = "./data/faiss"

    retrieve_k: int = 6
    naive_k: int = 5

    upper_threshold: float = 0.7
    lower_threshold: float = 0.3
    keep_threshold: float = 0.5
    judge_concurrency: int = 6

    web_top_n: int = 3
    web_supplement_n: int = 2
    web_domain_allowlist: Annotated[list[str], NoDecode] = Field(default_factory=list)

    langsmith_tracing: bool = True
    langsmith_api_key: str | None = None
    langsmith_project: str = "legal-crag"

    demo_api_key: str | None = None
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:5173"])
    rate_limit: str = "10/minute"
    query_log_enabled: bool = False

    @field_validator("web_domain_allowlist", "cors_origins", mode="before")
    @classmethod
    def parse_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "Settings":
        if not 0 <= self.lower_threshold < self.keep_threshold < self.upper_threshold <= 1:
            raise ValueError("Thresholds must satisfy LOWER < KEEP < UPPER")
        return self
