.PHONY: ingest test eval judge-dev api up lint smoke

PY := uv run --directory backend

ingest:
	$(PY) python -m app.ingest.fetch
	$(PY) python -m app.ingest.parse_gdpr
	$(PY) python -m app.ingest.parse_edpb
	$(PY) python -m app.ingest.chunk
	$(PY) python -m app.ingest.build_chroma
	$(PY) python -m app.ingest.build_faiss
	$(PY) python -m app.ingest.manifest

test:
	$(PY) pytest

lint:
	$(PY) ruff check .
	$(PY) ruff format --check .
	$(PY) mypy --explicit-package-bases --disable-error-code=call-arg app

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
