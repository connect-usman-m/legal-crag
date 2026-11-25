import type { QueryResponse } from "../../types/api";

type Props = { result: QueryResponse };

export default function AbstainCard({ result }: Props) {
  return (
    <section aria-label="Not enough evidence" className="rounded-card border border-dashed border-muted bg-surface p-5">
      <h2 className="mb-2 text-sm font-semibold text-muted">⊘ NOT ENOUGH EVIDENCE</h2>
      <p className="prose-answer">{result.answer}</p>
      <p className="mt-3 text-xs text-muted">
        Checked {result.chunk_scores?.length ?? 0} corpus chunks and {result.sources.length} sources. Try rephrasing or asking about the GDPR rule instead.
      </p>
    </section>
  );
}
