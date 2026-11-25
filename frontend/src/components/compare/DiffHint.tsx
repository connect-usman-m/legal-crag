import { buildDiffHint } from "../../lib/diffHint";
import type { CompareResponse } from "../../types/api";

export default function DiffHint({ payload }: { payload: CompareResponse }) {
  return (
    <div role="status" className="my-6 rounded-card border border-hairline bg-surface p-3 text-sm">
      <span className="mr-2 font-semibold text-muted">Difference:</span>
      {buildDiffHint(payload)}
    </div>
  );
}
