import type { ChunkScoreOut, Decision } from "../../types/api";
import { decisionToken } from "../../lib/decisionTokens";

type Props = { scores: ChunkScoreOut[]; decision: Decision; thresholds: Record<string, number> };

export default function WhyThisRoute({ scores, decision, thresholds }: Props) {
  const token = decisionToken(decision);
  const lower = thresholds.lower ?? 0.3;
  const keep = thresholds.keep ?? 0.5;
  const upper = thresholds.upper ?? 0.7;

  return (
    <details className="mt-6 rounded-card border border-hairline bg-surface">
      <summary className="cursor-pointer px-4 py-3 text-sm font-medium">
        ▸ Why this route? <span className="font-normal text-muted">({scores.length} chunks scored · {token.label})</span>
      </summary>
      <div className="overflow-x-auto px-4 pb-4">
        <table className="w-full min-w-[640px] border-collapse text-left text-xs">
          <caption className="sr-only">Retrieved chunk scores and decision thresholds</caption>
          <thead>
            <tr className="border-b border-hairline text-muted">
              <th scope="col" className="py-2 pr-3">Chunk</th>
              <th scope="col" className="py-2 pr-3">Score</th>
              <th scope="col" className="py-2 pr-3">Verdict</th>
              <th scope="col" className="py-2">Reason</th>
            </tr>
          </thead>
          <tbody>
            {scores.map((score) => (
              <tr key={score.chunk_id} className="border-b border-hairline last:border-0">
                <th scope="row" className={`py-2 pr-3 font-mono font-normal ${score.kept ? "" : "line-through text-muted"}`}>
                  {score.label}
                  {!score.kept && <span className="ml-1 font-sans not-italic">dropped</span>}
                </th>
                <td className="py-2 pr-3">
                  <div className="score-bar h-2 w-32 rounded-full">
                    <div
                      className="h-2 rounded-full bg-accent"
                      style={{ width: `${Math.max(0, Math.min(100, (score.score ?? 0) * 100))}%` }}
                    />
                  </div>
                  <span className="tabular">{score.score === null ? "not scored" : score.score.toFixed(2)}</span>
                </td>
                <td className="py-2 pr-3">{score.verdict ?? "—"}</td>
                <td className="py-2 text-muted">{score.reason ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-xs text-muted">
          Thresholds: lower {lower.toFixed(2)} · keep {keep.toFixed(2)} · upper {upper.toFixed(2)}.
          A chunk is kept when its score is at least keep.
        </p>
      </div>
    </details>
  );
}
