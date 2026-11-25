import assert from "node:assert/strict";
import test from "node:test";

import { decisionToken, isAbstained } from "../.test-dist/decisionTokens.js";

test("maps CRAG decisions to user-facing labels without red", () => {
  assert.equal(decisionToken("CORRECT").label, "Answered from corpus");
  assert.equal(decisionToken("AMBIGUOUS").label, "Corpus + web");
  assert.equal(decisionToken("INCORRECT").label, "Web fallback");
  assert.equal(decisionToken(null).label, "Naive RAG (no gate)");
  assert.match(decisionToken("INCORRECT").bgToken, /incorrect-bg/);
});

test("detects abstention from answer state", () => {
  assert.equal(isAbstained(true, "Some answer"), true);
  assert.equal(isAbstained(false, "NOT ENOUGH EVIDENCE: no sources"), true);
  assert.equal(isAbstained(false, "72 hours"), false);
});
