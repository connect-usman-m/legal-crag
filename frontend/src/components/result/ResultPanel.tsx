import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import AbstainCard from "./AbstainCard";
import AnswerBody from "./AnswerBody";
import ConfidenceMeter from "./ConfidenceMeter";
import DecisionBadge from "./DecisionBadge";
import OutsideCorpusBanner from "./OutsideCorpusBanner";
import SourceCard from "./SourceCard";
import TraceLink from "./TraceLink";
import WarningChips from "./WarningChips";
import WhyThisRoute from "./WhyThisRoute";
import { isAbstained } from "../../lib/decisionTokens";
import type { QueryResponse } from "../../types/api";

type Props = { result: QueryResponse };

export default function ResultPanel({ result }: Props) {
  const [highlighted, setHighlighted] = useState<string | null>(null);
  const maxScore = result.chunk_scores?.length
    ? Math.max(...result.chunk_scores.map((score) => score.score ?? 0))
    : null;
  const abstained = isAbstained(result.abstained, result.answer);

  useEffect(() => setHighlighted(null), [result.request_id]);

  const selectSource = (id: string) => {
    setHighlighted(id);
    document.getElementById(`source-${id}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  return (
    <section aria-live="polite" aria-label="Answer" className="mt-8">
      <div className="grid gap-8 lg:grid-cols-[3fr_2fr]">
        <div className="min-w-0">
          <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
            <div>
              <DecisionBadge decision={result.retrieval_decision} reason={result.decision_reason} maxScore={maxScore} />
              <p className="mt-2 text-xs text-muted">
                {result.mode === "crag" ? "Corrective RAG" : "Baseline"} · {result.latency_ms} ms
              </p>
            </div>
            {!abstained && <ConfidenceMeter value={result.confidence} label={result.confidence_label} />}
          </div>

          {result.retrieval_decision === "INCORRECT" && <OutsideCorpusBanner />}

          {abstained ? (
            <AbstainCard result={result} />
          ) : (
            <div className="rounded-card border border-hairline bg-surface p-5">
              <AnswerBody answer={result.answer} sources={result.sources} onSelect={selectSource} />
            </div>
          )}

          <WarningChips warnings={result.warnings} citationCoverage={result.citation_coverage} />

          {result.chunk_scores && result.thresholds && (
            <WhyThisRoute scores={result.chunk_scores} decision={result.retrieval_decision} thresholds={result.thresholds} />
          )}

          <div className="mt-6 flex flex-wrap gap-4 text-sm">
            <Link
              to={`/compare?q=${encodeURIComponent(result.question)}`}
              className="text-accent hover:underline"
            >
              Compare with Naive RAG
            </Link>
            <TraceLink url={result.trace_url} />
          </div>
        </div>

        <aside aria-label="Sources" className="min-w-0">
          <h2 className="mb-3 text-sm font-semibold text-muted">
            Sources ({result.sources.filter((source) => source.used).length} used)
          </h2>
          <div className="space-y-3">
            {result.sources.length === 0 && <p className="text-sm text-muted">No sources were considered.</p>}
            {result.sources.map((source, index) => (
              <div key={source.id} className={highlighted === source.id ? "source-flash rounded-card" : ""}>
                <SourceCard source={source} highlighted={highlighted === source.id} index={index} />
              </div>
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}
