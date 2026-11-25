import assert from "node:assert/strict";
import test from "node:test";

import { buildDiffHint } from "../.test-dist/diffHint.js";

test("explains web correction with the rejected corpus score", () => {
  const hint = buildDiffHint({
    naive: {
      answer: "Art. 83 fines [S1].",
      sources: [{ label: "GDPR Art. 83(5)" }],
      chunk_scores: [],
    },
    crag: {
      answer: "CCPA fines [S1].",
      sources: [{ label: "oag.ca.gov" }],
      retrieval_decision: "INCORRECT",
      chunk_scores: [{ label: "GDPR Art. 83(5)", score: 0.12, kept: false }],
    },
  });

  assert.match(hint, /GDPR Art\. 83\(5\)/);
  assert.match(hint, /0\.12/);
  assert.match(hint, /web sources/);
});

test("explains corpus-only agreement", () => {
  const hint = buildDiffHint({
    naive: { answer: "72 hours [S1].", sources: [], chunk_scores: [] },
    crag: {
      answer: "72 hours [S1].",
      sources: [],
      retrieval_decision: "CORRECT",
      chunk_scores: [{ label: "GDPR Art. 33(1)", score: 0.95, kept: true }],
    },
  });

  assert.match(hint, /kept corpus passages/);
});
