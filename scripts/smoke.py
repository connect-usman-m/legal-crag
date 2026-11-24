import os
import sys
from pathlib import Path

from langchain_groq import ChatGroq
from langsmith import traceable
from tavily import TavilyClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import Settings  # noqa: E402

REQUIRED_KEYS = ("GROQ_API_KEY", "TAVILY_API_KEY", "LANGSMITH_API_KEY")


@traceable(name="phase0_smoke")
def call_external_services(settings: Settings) -> dict[str, object]:
    llm = ChatGroq(
        model=settings.groq_judge_model,
        temperature=0,
        reasoning_effort=settings.groq_judge_reasoning_effort,
        api_key=settings.groq_api_key,
        timeout=20,
        max_retries=0,
    )
    reply = llm.invoke("Reply with the single word: ready")
    content = str(reply.content).strip()
    if not content:
        raise RuntimeError("Groq returned an empty response")

    client = TavilyClient(api_key=settings.tavily_api_key)
    results = client.search(
        "GDPR Article 33 breach notification deadline",
        search_depth="basic",
        max_results=1,
        include_answer=False,
        include_raw_content=False,
        timeout=8,
    )
    hits = results.get("results", [])
    if not hits:
        raise RuntimeError("Tavily returned no results")

    return {"groq_reply": content[:50], "tavily_hits": len(hits)}


def load_env_file(env_file: Path) -> None:
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        name = name.strip()
        if separator and name and not name.startswith("#") and name not in os.environ:
            os.environ[name] = value.strip()


def missing_api_keys(env: dict[str, str], env_file: Path) -> list[str]:
    present = {name for name, value in env.items() if name in REQUIRED_KEYS and value.strip()}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.partition("=")
            name = name.strip()
            if separator and name in REQUIRED_KEYS and value.strip():
                present.add(name)
    return [name for name in REQUIRED_KEYS if name not in present]


def main() -> int:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    load_env_file(env_file)
    missing = missing_api_keys(dict(os.environ), env_file)
    if missing:
        print("Missing API keys: " + ", ".join(missing))
        return 1

    settings = Settings()
    outcome = call_external_services(settings)
    print(f"Groq response: {outcome['groq_reply']}")
    print(f"Tavily results: {outcome['tavily_hits']}")
    print(f"LangSmith project: {settings.langsmith_project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
