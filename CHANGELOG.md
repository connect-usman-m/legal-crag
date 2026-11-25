# Changelog

## Slop cleanup

- Audited code and prose with the installed deslop and stop-slop skills.
- Removed no-op branches, duplicated calls and helpers, module-global request state, defensive wrappers, hardcoded trace metadata and dead UI labels.
- Consolidated answer-correctness logic into one tested helper and made trace metadata and report totals use runtime data.
- Rewrote flagged prose in the README, changelog, specs and UI strings.

## Phase 6 fixes

- Replaced the How it works diagram with the actual LangGraph topology and readable text in dark mode.
- Fixed the Ask button by wrapping its click handler instead of passing the React event into submission.
- Made dark mode the default theme before React loads.

## Phase 6 — Frontend, deployment and demo assets

- Added the React 18 + Vite + TypeScript frontend with Tailwind v4 tokens, TanStack Query and React Router.
- Implemented Ask, Compare, Results and How it works pages, including the decision badge, score table, citation chips, source cards, abstention state, warnings, dark mode and accessibility states.
- Added frontend Dockerfile, nginx config, Compose web service and Netlify deployment config.
- Added pure-logic tests for decision tokens, citation formatting and compare hints.
- Made LangSmith an optional health check so an invalid key does not block the UI.
- Demo GIF, screenshots and public deployment are missing. agent-browser was not installed, deployment credentials were unavailable, and the Compose build exceeded 10 minutes.

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
