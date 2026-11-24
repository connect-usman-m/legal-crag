.PHONY: ingest test eval judge-dev api up lint smoke

PY := uv run --directory backend

ingest:
	$(PY) python -m app.ingest.build_all

test:
	$(PY) pytest

lint:
	$(PY) ruff check .
	$(PY) ruff format --check .
	$(PY) mypy app

eval:
	$(PY) python -m eval.run_eval

judge-dev:
	$(PY) python -m eval.judge_dev

api:
	$(PY) uvicorn app.main:app --reload

up:
	docker compose up --build

smoke:
	$(PY) python ../scripts/smoke.py
