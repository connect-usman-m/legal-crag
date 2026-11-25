# Changelog

## Phase 5 — Evaluation harness and README

- Verified reference points against primary sources where reachable; recorded source URLs in the frozen test set.
- Added LLM grader, manual overrides, eval runner with answer/grade caches, and report generation.
- Generated `results.json` and `results.md` from the 15-question test set in both modes.
- Rewrote README with results table, architecture, setup, failure cases and limitations.

## Phase 4 — Generation, citations, API and tracing

- Added final structured generation prompt and citation enforcement with invalid-marker detection, coverage, renumbering and one corrective regeneration.
- Added confidence scoring, FastAPI app factory, `/query`, `/compare`, `/health`, `/corpus/stats` and `/eval/results` routes with error envelopes and request IDs.
- Added demo API-key security, CORS, slowapi rate limits, LangSmith root tracing metadata and trace links.
- Added backend Dockerfile with CPU-only torch, Compose service with data volume and TDD coverage for API contracts, citations, confidence and tracing.

## Phase 3 — Branches

- Added the `CRAGState` TypedDict with warning and timing reducers.
- Wrapped retrieval and evaluation as graph nodes and added `passthrough`, `web_correct` and `filter_supplement` branches.
- Added query rewriting, cross-encoder reranking with domain trust, Tavily search handling and separated corpus/web source lists.
- Added the compiled LangGraph builder, a temporary generator node and TDD coverage for branches, routing, reranking and web search.
- Made CI hermetic with placeholder keys, no scratchpad dependency and slow-test exclusion.

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
