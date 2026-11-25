import type { EvalRun } from "../../types/api";

const LABELS: Record<string, string> = {
  covered: "Covered",
  not_covered: "Not covered",
  ambiguous: "Ambiguous",
};

export default function CategoryChart({ run }: { run: EvalRun }) {
  const total = Math.max(1, run.records.filter((record) => record.mode === "crag").length / 3);
  return (
    <section className="mt-8 rounded-card border border-hairline bg-surface p-4">
      <h2 className="mb-4 font-serif text-lg">Correct answers by category</h2>
      <div className="space-y-4">
        {Object.entries(run.summary.by_category).map(([category, counts]) => (
          <div key={category}>
            <p className="mb-1 text-sm">{LABELS[category] ?? category}</p>
            {(["naive", "crag"] as const).map((mode) => (
              <div key={mode} className="mb-1 flex items-center gap-2 text-xs">
                <span className="w-12 text-muted">{mode === "crag" ? "CRAG" : "Naive"}</span>
                <div className="h-4 flex-1 border border-hairline bg-page">
                  <div
                    className={`h-full ${mode === "crag" ? "bg-accent" : "bg-decision-naive-fg"}`}
                    style={{ width: `${Math.min(100, ((counts[mode] ?? 0) / total) * 100)}%` }}
                  />
                </div>
                <span className="tabular w-8 text-right">{counts[mode] ?? 0}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}
