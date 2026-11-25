import type { EvalRun } from "../../types/api";

function Card({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <section className="rounded-card border border-hairline bg-surface p-4">
      <h2 className="text-xs text-muted">{label}</h2>
      <p className="mt-1 font-serif text-2xl tabular">{value}</p>
      <p className="mt-1 text-xs text-muted">{detail}</p>
    </section>
  );
}

export default function SummaryCards({ run }: { run: EvalRun }) {
  const abstentions = run.records.filter((record) => record.grade === "abstained");
  const appropriate = abstentions.filter((record) => record.answer_correct).length;
  const naive = run.summary.answer_accuracy.naive ?? 0;
  const crag = run.summary.answer_accuracy.crag ?? 0;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card label="Branch accuracy" value={`${Math.round(run.summary.branch_accuracy * 100)}%`} detail="CRAG decision matched the expected branch" />
      <Card label="Answer accuracy" value={`${Math.round(naive * 100)}% → ${Math.round(crag * 100)}%`} detail="Naive RAG → CRAG" />
      <Card
        label="Abstention appropriateness"
        value={abstentions.length ? `${Math.round((appropriate / abstentions.length) * 100)}%` : "n/a"}
        detail={`${appropriate}/${abstentions.length} abstentions accepted`}
      />
      <Card
        label="Citation validity"
        value={`${Math.round((run.summary.citation_validity.crag ?? 0) * 100)}%`}
        detail="CRAG answers with no invalid markers"
      />
    </div>
  );
}
