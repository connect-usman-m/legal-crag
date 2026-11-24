from app.llm.judge_cache import cache_key, cached_output, load_cache, save_cache
from app.schemas.llm import JudgeOutput


def test_cache_round_trip(tmp_path):
    path = tmp_path / "cache.json"
    output = JudgeOutput(score=0.95, verdict="relevant", reason="exact rule", jurisdiction_match=True)
    cache = {cache_key("V3", "question", "gdpr:art33:p1"): output.model_dump()}

    save_cache(cache, path)

    assert load_cache(path) == cache
    assert cached_output(load_cache(path), "V3", "question", "gdpr:art33:p1") == output
    assert cached_output(load_cache(path), "V3", "other", "gdpr:art33:p1") is None
