import assert from "node:assert/strict";
import test from "node:test";

import { splitCitations } from "../.test-dist/formatCitation.js";

test("splits answer text into citation buttons", () => {
  const parts = splitCitations("Deadline [S1] and reasons [S12].");

  assert.deepEqual(
    parts.map((part) => part.kind),
    ["text", "citation", "text", "citation", "text"],
  );
  assert.equal(parts[1].sourceId, "S1");
  assert.equal(parts[3].sourceId, "S12");
});

test("keeps malformed markers as text", () => {
  const parts = splitCitations("See [S0] and [Sx].");

  assert.equal(parts.some((part) => part.kind === "citation"), false);
  assert.equal(parts[0].text, "See [S0] and [Sx].");
});
