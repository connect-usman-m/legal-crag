# Changelog

## Phase 0 — Project setup

- Added the backend package skeleton and documented Python 3.11 dependency lockfile.
- Added validated `Settings` with the Phase 0 Groq model IDs and threshold ordering checks.
- Added TDD unit tests for configuration defaults, threshold validation, comma-separated lists and smoke-script key detection.
- Added `scripts/smoke.py` for a Groq call, a Tavily search and a LangSmith trace.
- Added `Makefile`, `.env.example`, `.gitignore`, GitHub Actions CI and this changelog.
