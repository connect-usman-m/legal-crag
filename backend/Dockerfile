FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    HF_HOME=/app/.cache/huggingface

RUN pip install --no-cache-dir uv==0.11.7

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/app ./app
COPY scripts ./scripts
RUN HF_HOME=/app/.cache/huggingface .venv/bin/python -c \
    "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('BAAI/bge-small-en-v1.5'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"
RUN .venv/bin/python -m app.ingest.fetch \
    && .venv/bin/python -m app.ingest.parse_gdpr \
    && .venv/bin/python -m app.ingest.parse_edpb \
    && .venv/bin/python -m app.ingest.chunk \
    && .venv/bin/python -m app.ingest.build_chroma \
    && .venv/bin/python -m app.ingest.build_faiss \
    && .venv/bin/python -m app.ingest.manifest

RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:${PATH}"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
