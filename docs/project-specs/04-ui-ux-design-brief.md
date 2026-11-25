# 04 — UI/UX Design Brief

**Project:** LexGate (`legal-crag`)
**Stack:** React 18 + Vite + TypeScript + Tailwind CSS (+ TanStack Query, React Router)
**Depends on:** 01-PRD, 03-App Flow
**Status:** Draft v1.0, 2026-11-24

---

## 1. Design goal

Show the retrieval decision above the answer: decision badge, chunk scores and source provenance.

### Principles
1. **Provenance before prose:** every statement is visibly tied to a source; corpus and web sources look different.
2. **Declining to answer is a feature:** the "Not enough evidence" state is designed as carefully as a successful answer.
3. **Show the machinery on demand:** the summary is visible at a glance; scores, reasons and traces are one click away.
4. **Trustworthy, not flashy:** a legal/editorial feel with calm colours and no chat-bubble gimmicks.

## 2. Audience and context of use

- **Primary:** a hiring manager or engineer on desktop, opening the demo from a README or CV link, spending 2–5 minutes.
- **Secondary:** someone curious about GDPR, possibly on mobile.
- They arrive with **no context**, so example questions must be one click away and labelled by category.

## 3. Visual direction

| Element | Direction |
|---|---|
| Mood | Editorial / legal publication: like a well-typeset statute annotated by a careful clerk |
| Typography | **Source Serif 4** for the answer body and headings (legal-document feel); **IBM Plex Sans** for UI chrome, labels and tables; **JetBrains Mono** for chunk IDs, scores and JSON |
| Base palette | Warm off-white background `#FAFAF7`, ink text `#1C1E21`, slate secondary `#5B6470`, hairline borders `#E4E2DC` |
| Accent | Deep indigo `#3B3FB6` for primary actions and links |
| Dark mode | Supported (`class` strategy); background `#121316`, surfaces `#1B1D21` |
| Density | Comfortable reading width (answer column max 68ch); data panels denser |
| Shape | 8px radius on cards, 999px on badges/chips; 1px borders preferred over shadows |
| Motion | Subtle: a 150–200 ms fade/slide for panels and a stepper progress animation; respects `prefers-reduced-motion` |

### Semantic colours (decision states)

Avoid red for `INCORRECT`. `INCORRECT` means the judge rejected weak evidence and switched sources. Red implies the answer is wrong.

| Decision | User-facing label | Colour token | Icon |
|---|---|---|---|
| `CORRECT` | **Answered from corpus** | emerald `#0F7B5F` / bg `#E6F4EF` | ✓ shield / book |
| `AMBIGUOUS` | **Corpus + web** | amber `#9A6700` / bg `#FBF3E0` | ◐ split |
| `INCORRECT` | **Web fallback** | sky/indigo `#2563A8` / bg `#E7F0FA` | ↻ globe |
| naive (`null`) | **Naive RAG (no gate)** | neutral slate `#5B6470` / bg `#EEF0F2` | — |
| abstained | **Not enough evidence** | slate with a dashed border | ⊘ |

Source-type tokens: **Corpus** = solid border with a book icon; **Web** = dashed border with a globe icon and the domain shown. Colour is never the only signal; there is always an icon and text.

## 4. Information architecture

Top bar: logo wordmark **LexGate**, nav (*Ask · Compare · Results · How it works*), GitHub link, dark-mode toggle.
Persistent footer: **"Not legal advice. Demo over GDPR + 3 EDPB guidelines. Web results may be inaccurate."**

## 5. Screens

### 5.1 Ask (`/`) — the main screen

```
┌──────────────────────────────────────────────────────────────────────────┐
│ LexGate        Ask  Compare  Results  How it works            ◐  GitHub  │
├──────────────────────────────────────────────────────────────────────────┤
│  Ask a question about EU data-protection law                             │
│  ┌──────────────────────────────────────────────────────────┐  [ Ask → ] │
│  │ Within how many hours must a breach be notified?         │            │
│  └──────────────────────────────────────────────────────────┘            │
│  Mode: (● CRAG) (○ Naive)                         0/500                  │
│  Try:  [Covered] Breach deadline  [Not covered] CCPA penalties           │
│        [Ambiguous] Meta fine & Art. 83  …                                │
├──────────────────────────────────────────────────────────────────────────┤
│  Retrieve ─✓─ Evaluate ─✓─ Passthrough ─✓─ Generate ─✓─ Cite ✓   3.2 s    │
├───────────────────────────────────────────┬──────────────────────────────┤
│ ✓ ANSWERED FROM CORPUS   Confidence ▮▮▮▮▯ │ SOURCES (2 used)             │
│                          High · 0.84      │ ┌──────────────────────────┐ │
│                                           │ │[S1] 📖 GDPR Art. 33(1)   │ │
│ A controller must notify the competent    │ │ Notification of a        │ │
│ supervisory authority without undue delay │ │ personal data breach…    │ │
│ and, where feasible, within 72 hours of   │ │ relevance 0.96 · corpus  │ │
│ becoming aware of the breach [S1]. Late   │ └──────────────────────────┘ │
│ notifications must give reasons [S1]…     │ ┌──────────────────────────┐ │
│                                           │ │[S2] 📖 EDPB 9/2022 §2.2  │ │
│ ▸ Why this route?  (6 chunks scored)      │ │ …                        │ │
│ ▸ Raw response JSON                       │ └──────────────────────────┘ │
│ [Compare with Naive RAG]  [View trace ↗]  │                              │
└───────────────────────────────────────────┴──────────────────────────────┘
```

**Components**
- `QuestionInput`: auto-growing textarea; Enter submits and Shift+Enter adds a newline; character counter; disabled while loading.
- `ModeToggle`: segmented control, CRAG (default) / Naive.
- `ExampleChips`: 6 chips (2 per category) with a small category tag. Clicking fills the input and submits.
- `PipelineStepper`: horizontal steps. Branch-specific labels: on INCORRECT the third step reads **Web search + re-rank**; on AMBIGUOUS, **Filter + supplement**. Without SSE (P2) the steps animate on a timer and then snap to the real path when the response arrives. Show total `latency_ms`.
- `DecisionBadge`: large badge with the label + icon; tooltip with `decision_reason`.
- `ConfidenceMeter`: 5-segment bar + label + number; info icon copy: "Heuristic: source relevance × citation coverage. Not a probability."
- `AnswerBody`: serif text. `[S#]` markers render as small superscript chips; hovering highlights the matching `SourceCard`, clicking scrolls to it and pulses it.
- `SourceCard`: citation label (e.g. "GDPR Art. 33(1)" or the web domain), title, 3-line excerpt (expandable), relevance score, type badge, external link icon (EUR-Lex/EDPB URL or web URL), "retrieved on" date for web.
- `WhyThisRoute` (collapsible): table of **all** retrieved chunks with a horizontal score bar, threshold lines at 0.3/0.5/0.7, the judge verdict and the reason; chunks dropped from context are struck through and labelled "dropped". This panel is the gate's evidence: render all chunk scores and threshold lines.
- `WarningChips`: e.g. `web_search_failed`, `low_citation_coverage`.
- `OutsideCorpusBanner` (INCORRECT only): "Outside the curated corpus (GDPR + EDPB). This answer uses web sources."
- `TraceLink`: opens the LangSmith trace in a new tab; hidden if there is no trace URL.

### 5.2 Not-enough-evidence state (first-class)
```
┌───────────────────────────────────────────────────────────┐
│ ⊘ NOT ENOUGH EVIDENCE                                     │
│ The available sources don't answer this question. The     │
│ corpus covers GDPR fining powers (Art. 83) but not        │
│ specific enforcement decisions, and web search returned   │
│ no authoritative source.                                  │
│ ▸ What was checked (6 chunks, 4 web results)              │
│ Try: rephrase · ask about the GDPR rule instead           │
└───────────────────────────────────────────────────────────┘
```
Dashed slate border, no confidence meter, the "Why this route?" panel still available. The card states what was checked and what was missing.

### 5.3 Compare (`/compare`)
- A single question input across the top; below it the **DiffHint** strip (see 03 §2.2).
- Two equal columns: **Naive RAG** | **CRAG**. Each is a compact version of the Ask result (badge, confidence, answer, source list, trace link). On mobile the columns become tabs (`Naive | CRAG`).
- Highlight the key contrast: if naive cited a corpus chunk that CRAG scored < 0.3, mark that source in the naive column with a small amber note: *"CRAG judged this chunk irrelevant (0.12)."* The GIF shows the judge rejecting evidence naive RAG used.

### 5.4 Results (`/eval`)
- **Summary cards (4):** Branch accuracy (CRAG), Answer accuracy Naive vs CRAG, Abstention appropriateness, Citation validity.
- **Category breakdown chart:** grouped bars (Covered / Not covered / Ambiguous) × (Naive, CRAG), showing correct answers out of 5. Two series, a consistent palette (naive slate, CRAG indigo), direct labels on the bars.
- **Results table:** columns `#`, Question, Category, Expected branch, CRAG branch (badge; ✓ if it matches), Naive result (✓ / ✗ / ⊘ / ~partial), CRAG result, Traces (two icon links). Sortable and filterable by category. Each row expands to show both answers.
- Run metadata footer: run date, model IDs, thresholds, prompt versions, corpus manifest hash.

### 5.5 How it works (`/how-it-works`)
- The graph diagram (SVG version of the TRD mermaid diagram) with the three branches colour-coded using the decision tokens.
- A threshold explainer: a 0–1 number line with LOWER/KEEP/UPPER marked and the three zones shaded.
- Corpus list with links, the "excluded on purpose" list, limitations (copied from TRD §13), and a link to the repo.

## 6. States checklist (every data view)

| State | Treatment |
|---|---|
| Empty (first visit) | Short intro line + example chips; no blank panels |
| Loading | Stepper animation + skeleton answer (3 serif lines) + skeleton source cards |
| Success | As designed above |
| Abstained | §5.2 |
| Partial / warnings | Answer + amber warning chips |
| Error 4xx/5xx | Inline banner with plain message + Retry; 429 shows a countdown |
| Index not ready | Full-page notice with the health detail |
| Offline | Banner: "You're offline" |

## 7. Responsive behaviour

| Breakpoint | Layout |
|---|---|
| ≥ 1024px | Two columns: answer (≈ 60%) + sources (≈ 40%) |
| 640–1023px | Single column; sources below the answer; stepper labels shortened |
| < 640px | Single column; stepper becomes "Step 3/5: Web search"; compare uses tabs; score table scrolls horizontally |

## 8. Accessibility (WCAG 2.1 AA)

- Text contrast ≥ 4.5:1 (check the badge colours on their tinted backgrounds).
- Decision and source types are always conveyed by **icon + text**, never colour alone.
- Citation chips are buttons with `aria-label="Source 1: GDPR Article 33(1)"`; keyboard focus moves to the source card.
- The stepper and result region use `aria-live="polite"` to announce "Answer ready — answered from corpus, high confidence".
- All interactive elements are reachable by Tab with visible focus rings (2px indigo outline).
- `prefers-reduced-motion` disables the stepper animation and pulses.
- Score bars include the numeric value as text.

## 9. Microcopy

| Context | Copy |
|---|---|
| Input placeholder | "Ask about GDPR, e.g. 'When must a DPO be appointed?'" |
| CORRECT tooltip | "Relevant passages were found in the curated corpus (top score {max}). Answer uses corpus only." |
| AMBIGUOUS tooltip | "Corpus passages were only partly relevant. Weak passages were dropped and web sources added." |
| INCORRECT tooltip | "No corpus passage was relevant (top score {max}). All were discarded and the answer uses web sources." |
| Confidence info | "A heuristic combining source relevance and citation coverage — not a probability of being correct." |
| Footer | "Not legal advice." |

## 10. Frontend component and folder map

```
frontend/src/
├── api/            client.ts (fetch + X-API-Key), queries.ts (TanStack hooks)
├── types/          api.ts  (mirrors 05-backend-schema response models)
├── components/
│   ├── layout/     TopBar, Footer
│   ├── query/      QuestionInput, ModeToggle, ExampleChips, PipelineStepper
│   ├── result/     DecisionBadge, ConfidenceMeter, AnswerBody, CitationChip,
│   │               SourceCard, WhyThisRoute, WarningChips, OutsideCorpusBanner,
│   │               AbstainCard, TraceLink, ResultPanel
│   ├── compare/    DiffHint, CompareColumns
│   └── eval/       SummaryCards, CategoryChart, ResultsTable
├── pages/          AskPage, ComparePage, ResultsPage, HowItWorksPage
├── lib/            decisionTokens.ts, formatCitation.ts, diffHint.ts
└── styles/         tailwind.css (CSS variables for tokens)
```

Tailwind: tokens defined as CSS variables in `:root` / `.dark`, mapped in `tailwind.config.ts` (`colors.decision.correct`, etc.), so badges and charts share the same source of truth.

## 11. Demo assets to produce

1. **Hero GIF (README top):** compare mode on "What are the penalties under the CCPA?". Naive cites GDPR Art. 83; CRAG shows *Web fallback* with a score table full of < 0.2 bars.
2. Three screenshots: one per decision branch, each with "Why this route?" expanded.
3. Three LangSmith trace screenshots, annotated with arrows pointing to `retrieval_decision`.
