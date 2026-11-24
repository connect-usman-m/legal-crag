# 05 — Backend Schema

**Project:** LexGate (`legal-crag`)
**Depends on:** 02-TRD, 03-App Flow
**Status:** Draft v1.0, 2026-11-24

This document defines every data shape in the backend: chunk records, vector-store metadata, LangGraph state, API request/response models, evaluation datasets and results, trace metadata, and the optional query log. Python code is Pydantic v2 / `TypedDict` and is meant to be copied into `app/schemas/` and `app/graph/state.py`.

---

## 1. Corpus data

### 1.1 `data/processed/chunks.jsonl` — single source of truth

One JSON object per line. Both Chroma and FAISS are built from this file.

```python
# app/schemas/corpus.py
from typing import Literal
from pydantic import BaseModel, Field

SourceId = Literal[
    "gdpr",
    "edpb_consent_05_2020",
    "edpb_breach_09_2022",
    "edpb_access_01_2022",
]
DocType = Literal["regulation_article", "regulation_recital", "guideline_section"]

class Chunk(BaseModel):
    chunk_id: str = Field(..., examples=["gdpr:art33:p1"])
    source_id: SourceId
    doc_type: DocType
    instrument: str = Field(..., examples=["Regulation (EU) 2016/679 (GDPR)"])
    jurisdiction: Literal["EU"] = "EU"
    effective_date: str = Field(..., examples=["2018-05-25"])   # ISO date
    version_date: str = Field(..., examples=["2016-05-04"])     # OJ publication / guideline version
    # Structural locators (None when not applicable)
    chapter: str | None = Field(None, examples=["IV"])
    chapter_title: str | None = None
    section: str | None = None
    article: int | None = Field(None, examples=[33])
    article_title: str | None = Field(None, examples=["Notification of a personal data breach to the supervisory authority"])
    paragraph: int | None = Field(None, examples=[1])
    recital: int | None = None
    guideline_section: str | None = Field(None, examples=["2.2"])
    # Display
    citation_label: str = Field(..., examples=["GDPR Art. 33(1)"])
    breadcrumb: str = Field(..., examples=["GDPR > Chapter IV > Section 2 > Article 33 > (1)"])
    url: str = Field(..., examples=["https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_33"])
    display_text: str                 # raw paragraph shown to users
    embed_text: str                   # breadcrumb + "\n\n" + display_text
    token_count: int
    content_hash: str                 # sha256(display_text) — idempotency
```

**Chunk ID conventions**

| Unit | Pattern | Example |
|---|---|---|
| Article paragraph | `gdpr:art{N}:p{P}` | `gdpr:art17:p3` |
| Article without paragraphs | `gdpr:art{N}` | `gdpr:art97` |
| Split oversized paragraph | `gdpr:art{N}:p{P}:part{K}` | `gdpr:art9:p2:part1` |
| Recital | `gdpr:rec{N}` | `gdpr:rec85` |
| Guideline chunk | `{source_id}:s{section}:c{NN}` | `edpb_consent_05_2020:s3.1.2:c02` |

### 1.2 `data/manifest.json`

```json
{
  "corpus_version": "gdpr_v1",
  "built_at": "2026-11-24T10:00:00Z",
  "embed_model": "BAAI/bge-small-en-v1.5",
  "embed_dim": 384,
  "chunker_version": "1.0.0",
  "sources": [
    {"source_id": "gdpr", "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679",
     "sha256": "…", "units": 272, "chunks": 610}
  ],
  "totals": {"chunks": 1480, "tokens": 412000},
  "stores": {"chroma_collection": "gdpr_v1", "faiss_index": "data/faiss/index.faiss"}
}
```
(Numbers are illustrative.)

## 2. Vector stores

### 2.1 Chroma — collection `gdpr_v1`

| Property | Value |
|---|---|
| Client | `chromadb.PersistentClient(path=CHROMA_DIR)` |
| Collection config | `configuration={"hnsw": {"space": "cosine"}}` (Chroma 1.x; **not** a `hnsw:space` metadata key — verified by a distance test). Metadata: `{"corpus_version": "gdpr_v1", "embed_model": "..."}` |
| `ids` | `chunk_id` |
| `documents` | `embed_text` |
| `embeddings` | normalized 384-dim vectors |
| `metadatas` | flat dict below |

Chroma metadata values must be `str | int | float | bool`, so **no `None` and no lists**. Leave out keys that would be `None`; don't set them to null.

```python
chroma_metadata = {
  "source_id": "gdpr",
  "doc_type": "regulation_article",
  "instrument": "Regulation (EU) 2016/679 (GDPR)",
  "jurisdiction": "EU",
  "effective_date": "2018-05-25",
  "article": 33,            # omitted when not applicable
  "paragraph": 1,
  "chapter": "IV",
  "citation_label": "GDPR Art. 33(1)",
  "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_33",
  "display_text": "In the case of a personal data breach, the controller shall …",
  "token_count": 118,
}
```
Similarity is returned as `1 - distance` (cosine).

### 2.2 FAISS — naive baseline

| File | Content |
|---|---|
| `data/faiss/index.faiss` | `faiss.IndexFlatIP(384)` over normalized vectors (inner product = cosine) |
| `data/faiss/docstore.json` | `{"ids": ["gdpr:art1:p1", …], "meta": {"gdpr:art1:p1": {…same flat metadata…}}}`. The row index in `ids` matches the FAISS row |
| `data/faiss/build.json` | `{"corpus_version", "embed_model", "n_vectors", "built_at"}` |

A startup check confirms that `n_vectors == chroma.count() == manifest.totals.chunks`. On a mismatch, `/health` returns `ready:false`.

## 3. Shared retrieval models

```python
# app/schemas/retrieval.py
from typing import Literal
from pydantic import BaseModel, Field

class RetrievedChunk(BaseModel):
    chunk_id: str
    citation_label: str
    url: str
    display_text: str
    source_id: str
    doc_type: str
    similarity: float = Field(..., ge=-1, le=1)     # vector similarity

class ChunkScore(BaseModel):
    chunk_id: str
    score: float | None = Field(None, ge=0, le=1)   # None = judge failed
    verdict: Literal["relevant", "partial", "irrelevant"] | None = None
    reason: str | None = None
    jurisdiction_match: bool | None = None
    kept: bool = False                               # survived KEEP_THRESHOLD into context
    error: bool = False

class WebResult(BaseModel):
    result_id: str                 # "web:{sha1(url)[:10]}"
    url: str
    domain: str
    title: str
    content: str                   # Tavily snippet
    tavily_score: float | None = None
    rerank_score: float            # sigmoid(cross-encoder)
    domain_trust: float            # 1.0 | 0.6 | 0.3
    final_score: float             # 0.8*rerank + 0.2*trust
    retrieved_at: str              # ISO datetime

class ContextSource(BaseModel):
    """A source as presented to the generator, numbered S1..Sn."""
    sid: str                       # "S1"
    kind: Literal["corpus", "web"]
    ref_id: str                    # chunk_id or result_id
    label: str                     # "GDPR Art. 33(1)" | "oag.ca.gov"
    title: str | None = None
    url: str
    text: str
    relevance: float               # judge score (corpus) | final_score (web) | similarity (naive)
```

## 4. LangGraph state

```python
# app/graph/state.py
from typing import Literal, TypedDict, Annotated
import operator
from app.schemas.retrieval import RetrievedChunk, ChunkScore, WebResult, ContextSource

Decision = Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]

class CitationReport(TypedDict):
    valid_ids: list[str]           # e.g. ["S1", "S3"]
    invalid_ids: list[str]         # markers not in context
    unused_ids: list[str]          # in context but never cited
    factual_sentences: int
    cited_sentences: int
    coverage: float                # cited / factual

class CRAGState(TypedDict, total=False):
    # input
    request_id: str
    question: str
    mode: Literal["crag", "naive"]
    # retrieve
    retrieved: list[RetrievedChunk]
    # evaluate
    chunk_scores: list[ChunkScore]
    retrieval_decision: Decision
    decision_reason: str
    # branches
    web_query: str | None
    web_results: list[WebResult]
    context_sources: list[ContextSource]
    # generate
    draft_answer: str
    used_source_ids: list[str]
    abstained: bool
    generation_attempts: int
    # cite
    answer: str
    sources: list[ContextSource]   # cited only, renumbered
    citation_report: CitationReport
    confidence: float
    confidence_label: Literal["High", "Medium", "Low", "None"]
    # cross-cutting
    warnings: Annotated[list[str], operator.add]     # reducer: nodes append
    timings_ms: Annotated[dict[str, int], lambda a, b: {**a, **b}]
```

**Node contracts** (each node returns a *partial* state dict):

| Node | Reads | Writes |
|---|---|---|
| `retrieve` | `question` | `retrieved`, `timings_ms.retrieve` |
| `evaluate` | `question`, `retrieved` | `chunk_scores`, `retrieval_decision`, `decision_reason`, `timings_ms.evaluate` |
| `passthrough` | `retrieved`, `chunk_scores` | `context_sources`, `chunk_scores` (kept flags) |
| `web_correct` | `question` | `web_query`, `web_results`, `context_sources`, `warnings?` |
| `filter_supplement` | `question`, `retrieved`, `chunk_scores` | `web_query`, `web_results`, `context_sources`, `chunk_scores`, `warnings?` |
| `generate` | `question`, `context_sources` | `draft_answer`, `used_source_ids`, `abstained`, `generation_attempts` |
| `cite` | `draft_answer`, `context_sources`, `retrieval_decision`, `chunk_scores` | `answer`, `sources`, `citation_report`, `confidence`, `confidence_label` |

**Routing function**

```python
def route_after_evaluate(state: CRAGState) -> str:
    return {
        "CORRECT": "passthrough",
        "INCORRECT": "web_correct",
        "AMBIGUOUS": "filter_supplement",
    }[state["retrieval_decision"]]
```

## 5. LLM structured outputs

```python
# app/schemas/llm.py
class JudgeOutput(BaseModel):
    score: float = Field(..., ge=0, le=1)
    verdict: Literal["relevant", "partial", "irrelevant"]
    reason: str = Field(..., max_length=240)
    jurisdiction_match: bool

class RewriteOutput(BaseModel):
    query: str = Field(..., max_length=200)

class GenerateOutput(BaseModel):
    answer: str
    used_source_ids: list[str]     # ["S1","S2"]
    abstained: bool

class GradeOutput(BaseModel):      # eval grader
    verdict: Literal["correct", "partial", "incorrect", "abstained"]
    unsupported_claims: int
    rationale: str
```

Prompts live in `app/llm/prompts.py` as constants named `{NAME}_V{n}` (e.g. `EVALUATOR_PROMPT_V1`, `GENERATE_PROMPT_V1`, `REWRITE_PROMPT_V1`, `GRADER_PROMPT_V1`). The active versions are exposed in `PROMPT_VERSIONS: dict[str, str]` and logged per request.

## 6. API schemas

### 6.1 `POST /query`

**Request**
```python
# app/schemas/api.py
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    mode: Literal["crag", "naive"] = "crag"
    debug: bool = False            # gates timings_ms only; chunk_scores is always present for mode="crag"
```

**Response**
```python
class SourceOut(BaseModel):
    id: str                        # "S1"
    type: Literal["corpus", "web"]
    label: str                     # "GDPR Art. 33(1)" | "edpb.europa.eu"
    title: str | None
    url: str
    snippet: str                   # ≤ 600 chars
    relevance_score: float
    used: bool                     # True for all in `sources` unless abstained

class ChunkScoreOut(BaseModel):
    chunk_id: str
    label: str
    score: float | None
    verdict: str | None
    reason: str | None
    kept: bool

class QueryResponse(BaseModel):
    request_id: str
    mode: Literal["crag", "naive"]
    question: str
    answer: str
    abstained: bool
    sources: list[SourceOut]
    retrieval_decision: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"] | None   # None for naive
    decision_reason: str | None
    confidence: float = Field(..., ge=0, le=1)
    confidence_label: Literal["High", "Medium", "Low", "None"]
    citation_coverage: float
    warnings: list[str]
    web_query: str | None = None
    chunk_scores: list[ChunkScoreOut] | None = None   # ALWAYS returned for mode="crag" (core demo feature); null only for naive
    trace_id: str | None
    trace_url: str | None
    latency_ms: int
    timings_ms: dict[str, int] | None = None   # gated by debug only
    models: dict[str, str]         # {"judge": "...", "generator": "...", "embed": "...", "rerank": "..."}
    prompt_versions: dict[str, str]
    thresholds: dict[str, float] | None = None   # crag only
```

**Example — INCORRECT branch**
```json
{
  "request_id": "b1f0…",
  "mode": "crag",
  "question": "What are the penalties for violating the CCPA?",
  "answer": "Under the CCPA, the California Attorney General can seek civil penalties per violation, with a higher amount for intentional violations [S1]. … [S2]",
  "abstained": false,
  "sources": [
    {"id": "S1", "type": "web", "label": "oag.ca.gov", "title": "California Consumer Privacy Act (CCPA)",
     "url": "https://oag.ca.gov/privacy/ccpa", "snippet": "…", "relevance_score": 0.88, "used": true}
  ],
  "retrieval_decision": "INCORRECT",
  "decision_reason": "max=0.18 (gdpr:art83:p5); 0 chunks ≥ 0.7; 0 chunks ≥ 0.3",
  "confidence": 0.58,
  "confidence_label": "Medium",
  "citation_coverage": 1.0,
  "warnings": [],
  "web_query": "CCPA civil penalties per violation intentional",
  "chunk_scores": [
    {"chunk_id": "gdpr:art83:p5", "label": "GDPR Art. 83(5)", "score": 0.18, "verdict": "irrelevant",
     "reason": "About GDPR fines; question concerns California law.", "kept": false}
  ],
  "trace_id": "8c2e…",
  "trace_url": "https://smith.langchain.com/…",
  "latency_ms": 5120,
  "models": {"judge": "openai/gpt-oss-20b", "generator": "openai/gpt-oss-120b",
             "embed": "BAAI/bge-small-en-v1.5", "rerank": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
  "prompt_versions": {"evaluator": "V1", "generate": "V1", "rewrite": "V1"},
  "thresholds": {"upper": 0.7, "lower": 0.3, "keep": 0.5}
}
```
(The answer text here is illustrative of the format, not a verified statement of CCPA amounts.)

### 6.2 `POST /compare`
```python
class CompareRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)

class CompareResponse(BaseModel):
    naive: QueryResponse
    crag: QueryResponse
```

### 6.3 Meta endpoints
```python
class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    ready: bool
    checks: dict[str, bool]   # chroma, faiss, embedder, reranker, groq_models, tavily_key, langsmith
    corpus_version: str | None

class CorpusStats(BaseModel):
    corpus_version: str
    built_at: str
    totals: dict[str, int]
    by_source: list[dict]     # {source_id, chunks, doc_type_counts}
```
`GET /eval/results` returns `EvalRun` (§7.3).

### 6.4 Error envelope
```python
class ErrorResponse(BaseModel):
    error: Literal["validation_error", "unauthorized", "rate_limited",
                   "upstream_unavailable", "index_not_ready", "timeout", "internal_error"]
    message: str
    request_id: str
    retry_after_s: int | None = None
```

| HTTP | `error` |
|---|---|
| 401 | unauthorized |
| 422 | validation_error |
| 429 | rate_limited |
| 503 | upstream_unavailable / index_not_ready |
| 504 | timeout |
| 500 | internal_error |

## 7. Evaluation data

### 7.1 Dataset item (`eval/datasets/*.jsonl`)

```python
class EvalItem(BaseModel):
    qid: str                                       # "T01"
    split: Literal["dev", "test"]
    category: Literal["covered", "not_covered", "ambiguous"]
    question: str
    expected_branch: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]
    reference_points: list[str]                   # facts a correct answer must contain
    expected_corpus_refs: list[str] = []          # e.g. ["gdpr:art33:p1"]
    acceptable_abstain: bool = False              # abstaining counts as correct
    notes: str | None = None
```

### 7.2 Test set (15, frozen) — draft

`reference_points` marked **[verify]** must be checked against a primary source during Phase 5 before the set is frozen. Out-of-corpus facts change, so don't rely on memory for them.

| qid | Category | Question | Expected branch | Reference points (draft) |
|---|---|---|---|---|
| T01 | covered | Within how many hours must a controller notify a personal data breach to the supervisory authority? | CORRECT | Without undue delay and where feasible within 72 hours of becoming aware; reasons required if late (Art. 33(1)) |
| T02 | covered | What are the lawful bases for processing personal data under the GDPR? | CORRECT | The six bases in Art. 6(1)(a)–(f) |
| T03 | covered | When is an organisation required to designate a Data Protection Officer? | CORRECT | Public authority; core activities of regular and systematic monitoring on a large scale; large-scale special categories / criminal data (Art. 37(1)) |
| T04 | covered | What is the maximum administrative fine for infringing the basic principles of processing? | CORRECT | Up to €20M or 4% of total worldwide annual turnover of the preceding year, whichever is higher (Art. 83(5)) |
| T05 | covered | How long does a controller have to respond to a data subject access request, and can it be extended? | CORRECT | One month; extendable by two further months, taking into account complexity and number of requests, with the data subject informed (Art. 12(3)); EDPB access guidelines |
| T06 | not_covered | What are the penalties for violating the California Consumer Privacy Act? | INCORRECT | Civil penalty amounts per violation / intentional violation **[verify]** |
| T07 | not_covered | What did the CJEU decide in the Schrems II judgment about the EU–US Privacy Shield? | INCORRECT | Privacy Shield invalidated; SCCs remain valid subject to case-by-case assessment **[verify]** |
| T08 | not_covered | What does HIPAA require for notifying individuals of a breach of unsecured health information? | INCORRECT | Notification timing and content under the HIPAA Breach Notification Rule **[verify]** |
| T09 | not_covered | What obligations does the EU AI Act place on providers of high-risk AI systems? | INCORRECT | Risk management, data governance, technical documentation, human oversight, etc. **[verify]** |
| T10 | not_covered | What is the role called that corresponds to a DPO under Brazil's LGPD? | INCORRECT | "Encarregado" **[verify]** |
| T11 | ambiguous | How much was Meta fined by the Irish DPC in 2023, and which GDPR article sets the maximum such fine? | AMBIGUOUS | Fine amount **[verify]** (web) + Art. 83 cap (corpus) |
| T12 | ambiguous | How does the GDPR 72-hour breach deadline compare with HIPAA's breach notification deadline? | AMBIGUOUS | Art. 33 (corpus) + HIPAA timing **[verify]** (web) |
| T13 | ambiguous | Can personal data be transferred to the US today, and under which GDPR transfer mechanisms? | AMBIGUOUS | Arts. 45/46/49 mechanisms (corpus) + current adequacy status of the EU–US Data Privacy Framework **[verify]** (web) |
| T14 | ambiguous | Do GDPR consent rules apply to cookie banners, and what does the ePrivacy Directive add? | AMBIGUOUS | Art. 4(11)/Art. 7 + EDPB consent guidelines (corpus) + ePrivacy Art. 5(3) **[verify]** (web) |
| T15 | ambiguous | Does the right to erasure apply to personal data used to train AI models? | AMBIGUOUS | Art. 17 grounds/exceptions (corpus) + current regulator guidance on AI **[verify]** (web); `acceptable_abstain: true` |

**Dev set (10, for threshold tuning only):** different questions with the same 4/3/3 category mix, e.g. "What is a personal data breach?", "What must a DPIA contain?", "What fines can the UK ICO impose?", "What is the deadline under the Virginia CDPA to respond to consumer requests?", "Does GDPR apply to a US company selling to EU customers, and how does US state law differ?"

### 7.3 Eval results (`eval/results/{run_id}/results.json`)

```python
class EvalRecord(BaseModel):
    qid: str
    category: str
    mode: Literal["naive", "crag"]
    expected_branch: str | None
    actual_branch: str | None
    branch_correct: bool | None           # crag only
    answer: str
    abstained: bool
    grade: Literal["correct", "partial", "incorrect", "abstained"]
    grade_source: Literal["llm", "manual"]
    answer_correct: bool                  # correct OR (abstained AND acceptable_abstain)
    unsupported_claims: int
    citation_valid: bool                  # no invalid markers
    citation_coverage: float
    confidence: float
    max_chunk_score: float | None
    sources: list[str]                    # labels
    latency_ms: int
    trace_url: str | None

class EvalSummary(BaseModel):
    branch_accuracy: float                # crag
    answer_accuracy: dict[str, float]     # {"naive": .., "crag": ..}
    by_category: dict[str, dict[str, int]]   # {"covered": {"naive": 5, "crag": 5}, …}
    hallucinations: dict[str, int]        # answers with unsupported_claims > 0
    citation_validity: dict[str, float]
    p50_latency_ms: dict[str, int]

class EvalRun(BaseModel):
    run_id: str                           # "2026-12-05T14-00Z_crag-v1"
    created_at: str
    split: Literal["dev", "test"]
    config: dict                          # models, thresholds, prompt versions, corpus manifest hash
    langsmith_experiment: str | None
    summary: EvalSummary
    records: list[EvalRecord]
```

`eval/manual_overrides.yaml` (human review always wins over the LLM grade):
```yaml
- qid: T11
  mode: naive
  grade: incorrect
  note: "Stated a fine amount not present in any source."
```

### 7.4 README table generated from `EvalRun`

| # | Category | Question (short) | Expected | CRAG branch | Naive | CRAG |
|---|---|---|---|---|---|---|
| T06 | Not covered | CCPA penalties | INCORRECT | INCORRECT ✓ | ✗ cited GDPR Art. 83 | ✓ |

Plus a per-category summary: rows Covered / Not covered / Ambiguous / **Total**, columns Naive ✓, CRAG ✓, CRAG branch accuracy.

## 8. LangSmith metadata schema

Root run (`crag_query` / `naive_query`):

| Key | Type | Example |
|---|---|---|
| `request_id` | str | `b1f0…` |
| `mode` | str | `crag` |
| `retrieval_decision` | str \| null | `INCORRECT` |
| `max_chunk_score` | float | `0.18` |
| `kept_chunks` | int | `0` |
| `web_results_used` | int | `3` |
| `abstained` | bool | `false` |
| `confidence` | float | `0.58` |
| `citation_coverage` | float | `1.0` |
| `warnings` | list[str] | `[]` |
| `thresholds` | dict | `{upper:.7, lower:.3, keep:.5}` |
| `prompt_versions` | dict | `{evaluator:"V1",…}` |
| `corpus_version` | str | `gdpr_v1` |
| `eval_qid` | str (eval only) | `T06` |

Tags: `mode:crag`, `decision:INCORRECT`, `env:local|demo|eval`.
Eval feedback keys: `branch_correct` (0/1), `answer_correct` (0/1), `citation_valid` (0/1), `unsupported_claims` (int).

## 9. Optional: query log (SQLite, off by default)

`QUERY_LOG_ENABLED=false`. When enabled, it supports demo analytics without collecting personal data.

```sql
CREATE TABLE query_log (
  request_id        TEXT PRIMARY KEY,
  created_at        TEXT NOT NULL,           -- ISO
  mode              TEXT NOT NULL CHECK (mode IN ('crag','naive')),
  question_hash     TEXT NOT NULL,           -- sha256; raw text not stored
  question_len      INTEGER NOT NULL,
  retrieval_decision TEXT,                   -- NULL for naive
  max_chunk_score   REAL,
  abstained         INTEGER NOT NULL,
  confidence        REAL NOT NULL,
  latency_ms        INTEGER NOT NULL,
  warnings          TEXT,                    -- JSON array
  trace_id          TEXT
);
CREATE INDEX idx_query_log_created ON query_log(created_at);
CREATE INDEX idx_query_log_decision ON query_log(retrieval_decision);
```

## 10. Settings model

```python
# app/core/config.py
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    groq_api_key: str
    groq_judge_model: str = "openai/gpt-oss-20b"
    groq_gen_model: str = "openai/gpt-oss-120b"
    groq_judge_reasoning_effort: Literal["low", "medium", "high"] = "low"
    embed_model: str = "BAAI/bge-small-en-v1.5"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    chroma_dir: str = "./data/chroma"
    chroma_collection: str = "gdpr_v1"
    faiss_dir: str = "./data/faiss"
    retrieve_k: int = 6
    naive_k: int = 5
    upper_threshold: float = 0.7
    lower_threshold: float = 0.3
    keep_threshold: float = 0.5
    judge_concurrency: int = 6
    tavily_api_key: str
    web_top_n: int = 3
    web_supplement_n: int = 2
    web_domain_allowlist: list[str] = []
    langsmith_project: str = "legal-crag"
    demo_api_key: str | None = None
    cors_origins: list[str] = ["http://localhost:5173"]
    rate_limit: str = "10/minute"
    query_log_enabled: bool = False

    def model_post_init(self, _):
        assert 0 <= self.lower_threshold < self.keep_threshold < self.upper_threshold <= 1, \
            "Thresholds must satisfy LOWER < KEEP < UPPER"
```
