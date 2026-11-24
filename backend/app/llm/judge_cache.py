import json
from pathlib import Path

from app.schemas.llm import JudgeOutput

CACHE_PATH = Path(__file__).resolve().parents[2] / "eval" / "results" / "judge_cache.json"


def cache_key(version: str, question: str, chunk_id: str) -> str:
    return f"{version}|{question}|{chunk_id}"


def load_cache(path: Path = CACHE_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(cache: dict[str, dict], path: Path = CACHE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def cached_output(cache: dict[str, dict], version: str, question: str, chunk_id: str) -> JudgeOutput | None:
    entry = cache.get(cache_key(version, question, chunk_id))
    return JudgeOutput.model_validate(entry) if entry else None
