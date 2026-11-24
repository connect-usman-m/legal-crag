import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_defaults_match_phase_zero_contract():
    settings = Settings(_env_file=None, groq_api_key="test-groq", tavily_api_key="test-tavily")

    assert settings.groq_judge_model == "openai/gpt-oss-20b"
    assert settings.groq_gen_model == "openai/gpt-oss-120b"
    assert settings.groq_judge_reasoning_effort == "low"
    assert settings.chroma_collection == "gdpr_v1"
    assert (settings.retrieve_k, settings.naive_k) == (6, 5)
    assert (settings.upper_threshold, settings.lower_threshold, settings.keep_threshold) == (
        0.7,
        0.3,
        0.5,
    )
    assert settings.judge_concurrency == 6
    assert (settings.web_top_n, settings.web_supplement_n) == (3, 2)
    assert settings.web_domain_allowlist == []
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.query_log_enabled is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"lower_threshold": 0.5},
        {"upper_threshold": 0.3},
        {"lower_threshold": 0.0, "keep_threshold": 0.0},
        {"keep_threshold": 1.0},
        {"lower_threshold": -0.1},
        {"upper_threshold": 1.1},
    ],
)
def test_thresholds_must_be_strictly_ordered_within_unit_interval(overrides):
    with pytest.raises(ValidationError, match="LOWER < KEEP < UPPER"):
        Settings(
            _env_file=None,
            groq_api_key="test-groq",
            tavily_api_key="test-tavily",
            **overrides,
        )


def test_comma_separated_env_lists_are_parsed():
    settings = Settings(
        _env_file=None,
        groq_api_key="test-groq",
        tavily_api_key="test-tavily",
        web_domain_allowlist="eur-lex.europa.eu, edpb.europa.eu",
        cors_origins="http://localhost:5173, http://localhost:4173",
    )

    assert settings.web_domain_allowlist == ["eur-lex.europa.eu", "edpb.europa.eu"]
    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:4173"]


def test_missing_api_keys_are_rejected(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
