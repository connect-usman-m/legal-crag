# Evaluation results

Run: `2026-11-25T06-44Z_crag-v1` — split: `test`

## Per-question results

| # | Category | Naive | CRAG | CRAG branch | Naive trace | CRAG trace |
|---|---|---|---|---|---|---|
| T01 | covered | ✗ | ✗ | ✓ | - | - |
| T02 | covered | ✓ | ✓ | ✓ | - | - |
| T03 | covered | ✓ | ✗ | ✓ | - | - |
| T04 | covered | ✓ | ✓ | ✓ | - | - |
| T05 | covered | ✓ | ✓ | ✓ | - | - |
| T06 | not_covered | ✗ | ✓ | ✓ | - | - |
| T07 | not_covered | ✗ | ✗ | ✓ | - | - |
| T08 | not_covered | ✗ | ✓ | ✓ | - | - |
| T09 | not_covered | ✗ | ✓ | ✓ | - | - |
| T10 | not_covered | ✗ | ✗ | ✓ | - | - |
| T11 | ambiguous | ✗ | ✓ | ✓ | - | - |
| T12 | ambiguous | ✗ | ✓ | ✓ | - | - |
| T13 | ambiguous | ✗ | ✓ | ✓ | - | - |
| T14 | ambiguous | ✗ | ✓ | ✗ | - | - |
| T15 | ambiguous | ✓ | ✗ | ✓ | - | - |

## By category

| Category | Naive correct | CRAG correct |
|---|---:|---:|
| Covered | 4/5 | 3/5 |
| Not covered | 0/5 | 3/5 |
| Ambiguous | 1/5 | 4/5 |

## Summary

- Branch accuracy (CRAG): 93%
- Answer accuracy: naive 33%, CRAG 67%
- Citation validity: naive 100%, CRAG 100%
- p50 latency (ms): naive 9379, CRAG 15427

Trace links are shown when LangSmith tracing is enabled and the API key is valid.
