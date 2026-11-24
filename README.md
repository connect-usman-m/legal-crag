# LexGate

Legal document QA with Corrective RAG over GDPR and selected EDPB guidelines.

## Status

Phase 0 (project setup) is complete. The ingestion pipeline, graph and UI land in later phases.

## Setup

Requires Python 3.11 and `uv`.

```bash
cp .env.example .env
# Fill in GROQ_API_KEY, TAVILY_API_KEY and LANGSMITH_API_KEY in .env
uv sync --directory backend
```

## Development

```bash
make lint
make test
make smoke
```

`make smoke` performs one Groq call, one Tavily search and one traced LangSmith run. It fails early if any required key is missing.
