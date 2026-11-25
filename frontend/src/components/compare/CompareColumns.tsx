import { useState } from "react";

import AnswerBody from "../result/AnswerBody";
import ConfidenceMeter from "../result/ConfidenceMeter";
import DecisionBadge from "../result/DecisionBadge";
import SourceCard from "../result/SourceCard";
import { decisionToken, isAbstained } from "../../lib/decisionTokens";
import type { QueryResponse } from "../../types/api";

type Props = { naive: QueryResponse; crag: QueryResponse };

function CompactResult({ result, naiveResult }: { result: QueryResponse; naiveResult?: QueryResponse }) {
  const score = result.chunk_scores?.find(
    (chunk) => !chunk.kept && naiveResult?.sources.some((source) => source.label === chunk.label),
  );
  return (
    <section className="rounded-card border border-hairline bg-surface p-4">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <DecisionBadge decision={result.retrieval_decision} reason={result.decision_reason} maxScore={score?.score ?? null} />
        <ConfidenceMeter value={result.confidence} label={result.confidence_label} />
      </div>
      {isAbstained(result.abstained, result.answer) ? (
        <p className="prose-answer text-muted">⊘ Not enough evidence. {result.answer}</p>
      ) : (
        <AnswerBody answer={result.answer} sources={result.sources} onSelect={() => undefined} />
      )}
      {score && (
        <p className="mt-3 rounded-card bg-decision-ambiguous-bg p-2 text-xs text-decision-ambiguous-fg">
          CRAG judged this chunk irrelevant ({score.score?.toFixed(2) ?? "n/a"}).
        </p>
      )}
      <h3 className="mt-4 text-xs font-semibold text-muted">Sources</h3>
      <ul className="mt-2 space-y-2">
        {result.sources.map((source, index) => (
          <li key={source.id}>
            <SourceCard source={source} highlighted={false} index={index} />
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function CompareColumns({ naive, crag }: Props) {
  const [tab, setTab] = useState<"naive" | "crag">("crag");
  return (
    <div>
      <div className="mb-3 flex gap-2 md:hidden" role="tablist" aria-label="Compare modes">
        {(["naive", "crag"] as const).map((mode) => (
          <button
            key={mode}
            type="button"
            role="tab"
            aria-selected={tab === mode}
            className={`flex-1 rounded-card border px-3 py-2 text-sm ${
              tab === mode ? "border-accent text-ink" : "border-hairline text-muted"
            }`}
            onClick={() => setTab(mode)}
          >
            {decisionToken(mode === "crag" ? crag.retrieval_decision : null).label}
          </button>
        ))}
      </div>
      <div className="hidden grid-cols-2 gap-6 md:grid">
        <div>
          <h2 className="mb-3 font-serif text-lg">Naive RAG</h2>
          <CompactResult result={naive} />
        </div>
        <div>
          <h2 className="mb-3 font-serif text-lg">CRAG</h2>
          <CompactResult result={crag} naiveResult={naive} />
        </div>
      </div>
      <div className="md:hidden">
        <h2 className="mb-3 font-serif text-lg">{tab === "crag" ? "CRAG" : "Naive RAG"}</h2>
        {tab === "crag" ? <CompactResult result={crag} naiveResult={naive} /> : <CompactResult result={naive} />}
      </div>
    </div>
  );
}
