# 01 — Product Requirements Document (PRD)

**Project:** Legal Document QA with Corrective RAG (working name: **LexGate**)
**Repo name:** `legal-crag`
**Owner:** Muhammad Usman Akram
**Type:** Portfolio project (open source, public demo)
**Status:** Draft v1.0, 2026-11-24

---

## 1. Summary

LexGate answers questions about EU data-protection law (GDPR and selected EDPB guidelines) with sources attached. Before it writes an answer, it **checks the retrieved evidence and says whether that evidence was good enough**. If the evidence is weak, it fetches better evidence from the web or declines to answer. It never quietly makes something up.

It implements **Corrective RAG (CRAG)** as a LangGraph state machine. A relevance gate sits between retrieval and generation and routes every query to one of three branches:

| Decision | Meaning | Action |
|---|---|---|
| `CORRECT` | At least one retrieved chunk is clearly relevant | Keep the relevant chunks and generate from the corpus only |
| `AMBIGUOUS` | Retrieved chunks are partly relevant | Drop weak chunks, add re-ranked web results, generate from both |
| `INCORRECT` | No retrieved chunk is relevant | Discard the chunks, run a web search, re-rank, generate from web results only |

The decision is returned in every API response (`retrieval_decision`), shown in the UI and recorded on every LangSmith trace.

## 2. Problem statement

Standard RAG always runs *retrieve → generate*. On legal text this fails without any warning:

- **Wrong jurisdiction:** a question about CCPA penalties retrieves GDPR Article 83, and the model confidently answers with GDPR fines.
- **Wrong instrument or time period:** a question about the EU AI Act retrieves GDPR Article 22 (automated decisions), and the answer mixes the two laws.
- **Partial coverage:** a question about a specific enforcement fine retrieves the article that caps fines, and the model invents the actual amount.

In a legal setting a confident wrong answer does more harm than no answer. Users can't tell from the output that retrieval failed.

## 3. Goals

| # | Goal | Measured by |
|---|---|---|
| G1 | Detect when retrieved evidence is irrelevant or partial before generating | Branch accuracy on the 15-question test set (target ≥ 12/15) |
| G2 | Never state a fact that has no source | Citation validity = 100% (every citation marker points to a source in context); unsupported-claim rate ≤ 1/15 |
| G3 | Make the corrective logic visible | `retrieval_decision` and per-chunk scores in the API, the UI and LangSmith |
| G4 | Show a measurable improvement over naive RAG | Comparison table: CRAG correct answers ≥ naive + 4 on the 15 questions, with the gain concentrated in the "not covered" and "ambiguous" categories |
| G5 | Be easy to run and review | `docker compose up` works from a clean clone; public demo URL; README with the results table and trace screenshots |

## 4. Non-goals

- Legal advice, or production use by lawyers. The UI says **"Not legal advice"** throughout.
- Multi-jurisdiction coverage in the corpus. The corpus is EU-only on purpose so that out-of-corpus questions are easy to construct.
- User accounts, chat history or multi-turn conversation (single-turn QA only).
- Fine-tuning the evaluator. CRAG's paper fine-tunes T5 as the evaluator; this project uses an LLM-as-judge prompt instead and says so.
- Uploading your own documents through the UI (possible stretch goal).

## 5. Target users and personas

| Persona | Need | What they look at |
|---|---|---|
| **Hiring manager / tech interviewer** (primary) | Judge in about 5 minutes whether Waleed understands production RAG | README results table, live demo, LangSmith trace screenshots, `retrieval_decision` in the response |
| **Engineer reviewing the repo** | Check code quality, graph design and test discipline | `graph/`, `nodes/`, tests, eval harness, Docker setup |
| **Curious end user** | Get a sourced answer to a GDPR question | Query page, citations, the "Not enough evidence" state |

## 6. Corpus scope

The core corpus is fixed and versioned, with a hash of every source file stored in the ingestion manifest.

| Source | Content | Why it's included |
|---|---|---|
| Regulation (EU) 2016/679 (GDPR), EUR-Lex CELEX `32016R0679`, English consolidated text | 99 articles, 173 recitals, 11 chapters | Primary law; clean structure with stable citation IDs (Art. 17(1)) |
| EDPB Guidelines 05/2020 on consent | PDF guideline | Adds interpretation depth for consent questions |
| EDPB Guidelines 9/2022 on personal data breach notification | PDF guideline | Practical examples to pair with Articles 33–34 |
| EDPB Guidelines 01/2022 on data subject rights: right of access | PDF guideline | Practical detail to pair with Article 15 |

**Deliberately excluded** (so they serve as "not covered" test material): CCPA/CPRA, HIPAA, the UK GDPR and Data (Use and Access) Act, the EU AI Act, the ePrivacy Directive, CJEU case law (Schrems II etc.), and enforcement decisions and fines.

Every chunk carries `jurisdiction = "EU"`, `instrument`, `effective_date`, and an article/recital/section citation. This metadata is what lets the UI and the generator label a source as "GDPR Art. 33(1)" rather than "chunk_0412".

## 7. User stories

### Querying
- **US-1** As a user, I can type a question and get an answer with numbered inline citations `[S1]` that link to the exact source.
- **US-2** As a user, I can see which branch fired (*Answered from corpus* / *Corpus + web* / *Web fallback*) and why: the per-chunk relevance scores.
- **US-3** As a user, I can see a confidence level (High / Medium / Low) and the number behind it.
- **US-4** As a user, when the system lacks evidence, I get a clear **"Not enough evidence to answer"** response rather than a guess.
- **US-5** As a user, I can see which sources come from the curated corpus and which come from the web, distinguished visually.

### Comparison and transparency
- **US-6** As a reviewer, I can run the same question through **Naive RAG** and **CRAG** side by side.
- **US-7** As a reviewer, I can open the LangSmith trace for any answer from a link in the UI or the API response.
- **US-8** As a reviewer, I can browse the evaluation results (15 questions × 2 modes) in the UI and in the README.

### Developer
- **US-9** As a developer, I can rebuild the Chroma and FAISS indexes from raw sources with one command (`make ingest`).
- **US-10** As a developer, I can run the full evaluation with one command (`make eval`), which writes `results.json`, `results.md` and a LangSmith dataset/experiment.
- **US-11** As a developer, I can change thresholds and model IDs through environment variables without editing code.

## 8. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Ingest the GDPR (HTML) and EDPB guidelines (PDF) into structure-aware chunks with citation metadata | P0 |
| FR-2 | Embed chunks with a local Hugging Face model; write them to **Chroma** (CRAG retriever) and **FAISS** (naive baseline) from the same `chunks.jsonl` | P0 |
| FR-3 | Naive RAG pipeline: FAISS top-k → generate (same generator prompt as CRAG) | P0 |
| FR-4 | LangGraph CRAG graph: `retrieve → evaluate → {passthrough \| web_correct \| filter_supplement} → generate → cite` | P0 |
| FR-5 | The evaluator scores **each chunk independently** on a 0–1 scale through an LLM-as-judge with structured JSON output | P0 |
| FR-6 | Decision rule with configurable `UPPER` / `LOWER` / `KEEP` thresholds (see TRD §6) | P0 |
| FR-7 | The INCORRECT branch rewrites the query, calls Tavily and re-ranks the results with a cross-encoder | P0 |
| FR-8 | The AMBIGUOUS branch filters chunks below `KEEP`, then merges them with re-ranked web results | P0 |
| FR-9 | The generator may only state facts from sources in its context; each claim carries a `[S#]` marker; it abstains when evidence is insufficient | P0 |
| FR-10 | The cite node validates citation markers, drops unused sources and computes citation coverage | P0 |
| FR-11 | `POST /query` returns `answer`, `sources`, `retrieval_decision`, `confidence` (plus extra fields; see the backend schema) | P0 |
| FR-12 | LangSmith tracing with `retrieval_decision` as run metadata and a tag on the root run | P0 |
| FR-13 | Evaluation harness: 15 labelled questions (5 covered / 5 not covered / 5 ambiguous), both modes, results table | P0 |
| FR-14 | React UI: query page, side-by-side compare, eval results page | P1 |
| FR-15 | Docker Compose for API + web; public demo deploy | P1 |
| FR-16 | Streaming node progress (SSE) to the UI | P2 |
| FR-17 | Knowledge-strip refinement (decompose-then-recompose, as in the CRAG paper) on CORRECT | P2 |
| FR-18 | Run the evaluator on web results as well (gate both sources) | P2 |

## 9. Non-functional requirements (summary — details in the TRD)

- **Latency:** Naive p50 ≤ 2.5 s; CRAG CORRECT p50 ≤ 4 s; AMBIGUOUS/INCORRECT p50 ≤ 6 s and p95 ≤ 10 s; timeouts: Groq 20 s, Tavily 8 s, overall request 30 s.
- **Cost:** stays within the Groq and Tavily free tiers for the demo; the public demo is rate limited.
- **Reproducibility:** pinned dependencies, a versioned corpus manifest, temperature 0, and recorded eval run IDs.
- **Observability:** 100% of queries traced in LangSmith when `LANGSMITH_TRACING=true`.
- **Safety:** "Not legal advice" disclaimer, abstention behaviour, and a domain allowlist for web search.

## 10. Success metrics (portfolio outcomes)

1. A README results table with a visible CRAG improvement in the "not covered" and "ambiguous" rows.
2. At least 3 annotated LangSmith trace screenshots, one per branch.
3. A 60–90 s demo video/GIF of side-by-side compare mode on a wrong-jurisdiction question (e.g., CCPA penalties).
4. A clean clone gets to a working demo in under 10 minutes using the README.

## 11. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The LLM judge is miscalibrated (scores cluster around 0.5) | Wrong branch fires | Rubric with anchored score bands, few-shot examples, temperature 0; tune thresholds on a **separate dev set** (not the 15 test questions) |
| Overfitting thresholds to the 15 test questions | Inflated results | 10-question dev set for tuning; the 15-question test set is frozen and run once per release |
| Groq rate limits during per-chunk parallel judging | 429 errors and latency spikes | Bounded concurrency, retry with exponential backoff, small judge model |
| Web results bring in low-quality legal content | Bad answers on the web branches | Domain allowlist / trust weighting (eur-lex, edpb, ico, official regulators), cross-encoder re-rank, citations always shown |
| Groq model IDs get deprecated | Broken demo | Model IDs in config; health check verifies them on startup |
| The demo burns API credits | Cost | API key on the demo, per-IP rate limit, cached responses for example questions |

## 12. Open questions

1. Should compare mode also show a **"naive + always web"** baseline to isolate the effect of the gate from the effect of web access? (Recommended as a stretch goal: it makes the analysis more convincing.)
2. Should answers on the INCORRECT branch carry an explicit "outside the curated corpus" warning banner? (Proposed: yes.)
3. Where to host the demo: Hugging Face Spaces (Docker, enough RAM for local models) plus Netlify for the frontend is the current proposal.

## 13. Milestones

| Milestone | Content | Doc |
|---|---|---|
| M1 | Ingestion + naive baseline | 06 §Phase 1 |
| M2 | Evaluator node calibrated on the dev set | 06 §Phase 2 |
| M3 | All three branches wired | 06 §Phase 3 |
| M4 | API + citation enforcement + tracing | 06 §Phase 4 |
| M5 | Eval harness + README table | 06 §Phase 5 |
| M6 | UI + Docker + deploy | 06 §Phase 6 |
