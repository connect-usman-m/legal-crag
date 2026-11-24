# Changelog

## Phase 2 — CRAG evaluator node

- Added dev and test datasets, explicit hand labels and a recorded-judgment cache for reproducible calibration.
- Added pure `decide()` and `select_kept()` functions with boundary tests.
- Added an LLM-as-judge evaluator with strict Groq JSON-schema output, bounded concurrency, retry handling and prompt-version metadata.
- Added calibration analysis and report: 9/10 dev branch accuracy and 28/29 irrelevant chunks below LOWER.

## Phase 1 — Ingestion + baseline RAG

- Added TDD coverage for GDPR/EDPB parsing, chunking, Chroma cosine configuration, manifest validation, retrieval recall and naive citation handling.
- Added source fetching, structure-aware chunking and reproducible Chroma + FAISS index builds from one `chunks.jsonl`.
- Added the bge-small embedder singleton, retrieval stores and a 10-question recall sanity test.
- Added the naive RAG pipeline with `GENERATE_PROMPT_V1` and `scripts/try_naive.py`.

## Phase 0 — Project setup

- Added the backend package skeleton and documented Python 3.11 dependency lockfile.
- Added validated `Settings` with the Phase 0 Groq model IDs and threshold ordering checks.
- Added TDD unit tests for configuration defaults, threshold validation, comma-separated lists and smoke-script key detection.
- Added `scripts/smoke.py` for a Groq call, a Tavily search and a LangSmith trace.
- Added `Makefile`, `.env.example`, `.gitignore`, GitHub Actions CI and this changelog.
