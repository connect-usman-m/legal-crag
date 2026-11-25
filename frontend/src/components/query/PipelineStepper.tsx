import { useEffect, useState } from "react";

import type { Decision } from "../../types/api";

type Props = { loading: boolean; decision: Decision };

function labels(decision: Decision): string[] {
  const branch = decision === "INCORRECT" ? "Web search + re-rank" : decision === "AMBIGUOUS" ? "Filter + supplement" : "Passthrough";
  return ["Retrieve", "Evaluate", branch, "Generate", "Cite"];
}

export default function PipelineStepper({ loading, decision }: Props) {
  const steps = labels(decision);
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (!loading) {
      setActive(steps.length - 1);
      return;
    }
    setActive(0);
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = window.setInterval(() => setActive((value) => Math.min(value + 1, steps.length - 1)), 450);
    return () => window.clearInterval(timer);
  }, [loading, steps.length]);

  return (
    <div aria-live="polite" className="overflow-x-auto border-y border-hairline py-3 text-xs">
      <ol className="flex min-w-max items-center gap-2">
        {steps.map((step, index) => (
          <li key={step} className="flex items-center gap-2">
            <span
              className={`flex items-center gap-1 rounded-full px-2 py-1 ${
                index <= active ? "bg-decision-correct-bg text-decision-correct-fg" : "bg-page text-muted"
              }`}
            >
              <span aria-hidden="true">{index < active ? "✓" : index === active ? "●" : "○"}</span>
              <span>{step}</span>
            </span>
            {index < steps.length - 1 && <span aria-hidden="true" className="text-muted">─</span>}
          </li>
        ))}
      </ol>
      <p className="sr-only">{loading ? `Step ${active + 1} of ${steps.length}` : "Pipeline complete"}</p>
    </div>
  );
}
