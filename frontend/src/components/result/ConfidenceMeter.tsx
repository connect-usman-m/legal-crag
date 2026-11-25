type Props = { value: number; label: string };

export default function ConfidenceMeter({ value, label }: Props) {
  const filled = Math.round(value * 5);
  return (
    <div className="text-right text-xs text-muted">
      <div className="mb-1">{label} · <span className="tabular">{value.toFixed(2)}</span></div>
      <div
        className="inline-flex gap-1"
        role="img"
        aria-label={`Confidence ${label}, ${value.toFixed(2)}. Heuristic, not a probability.`}
        title="Heuristic: source relevance × citation coverage. Not a probability."
      >
        {[0, 1, 2, 3, 4].map((segment) => (
          <span
            key={segment}
            aria-hidden="true"
            className={`h-2 w-4 rounded-sm ${segment < filled ? "bg-accent" : "border border-hairline bg-surface"}`}
          />
        ))}
      </div>
    </div>
  );
}
