from typing import Any

from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from pydantic import SecretStr

from app.core.config import Settings
from app.schemas.llm import JudgeOutput


def get_judge(settings: Settings | None = None) -> Runnable[Any, Any]:
    config = settings or Settings()
    return ChatGroq(
        model=config.groq_judge_model,
        temperature=0,
        reasoning_effort=config.groq_judge_reasoning_effort,
        api_key=SecretStr(config.groq_api_key),
        timeout=20,
        max_retries=2,
    ).with_structured_output(JudgeOutput, method="json_schema", strict=True)
