import importlib.util
from pathlib import Path

SMOKE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "smoke.py"
_SPEC = importlib.util.spec_from_file_location("phase0_smoke", SMOKE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
smoke = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(smoke)


def test_missing_keys_detected_from_environment(tmp_path):
    env = {"GROQ_API_KEY": "set", "TAVILY_API_KEY": "", "LANGSMITH_API_KEY": "  "}

    assert smoke.missing_api_keys(env, tmp_path / "missing.env") == [
        "TAVILY_API_KEY",
        "LANGSMITH_API_KEY",
    ]


def test_missing_keys_detected_from_dotenv(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=from-file\nTAVILY_API_KEY=\nLANGSMITH_API_KEY=from-file\n",
        encoding="utf-8",
    )

    assert smoke.missing_api_keys({}, env_file) == ["TAVILY_API_KEY"]


def test_all_keys_present_returns_empty_list(tmp_path):
    env = {name: "value" for name in smoke.REQUIRED_KEYS}

    assert smoke.missing_api_keys(env, tmp_path / "missing.env") == []


def test_load_env_file_sets_only_absent_variables(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\nNEW_KEY=from-file\nGROQ_API_KEY=keep-existing\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("NEW_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "already-set")

    smoke.load_env_file(env_file)

    assert smoke.os.environ["NEW_KEY"] == "from-file"
    assert smoke.os.environ["GROQ_API_KEY"] == "already-set"
