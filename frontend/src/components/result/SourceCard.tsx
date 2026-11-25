import type { SourceOut } from "../../types/api";

type Props = { source: SourceOut; highlighted: boolean; index: number };

export default function SourceCard({ source, highlighted, index }: Props) {
  const isWeb = source.type === "web";
  const domain = (() => {
    try {
      return new URL(source.url).hostname;
    } catch {
      return source.url;
    }
  })();

  return (
    <article
      id={`source-${source.id}`}
      className={`rounded-card border bg-surface p-3 text-sm ${isWeb ? "border-dashed" : ""} ${
        highlighted ? "border-accent source-flash" : "border-hairline"
      }`}
    >
      <div className="mb-1 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <span className="mr-1 font-mono text-xs text-accent">[{source.id}]</span>
          <span aria-hidden="true">{isWeb ? "🌐" : "📖"}</span>{" "}
          <span className="font-medium">{isWeb ? domain : source.label}</span>
          <p className="text-xs text-muted">{isWeb ? source.label : source.title ?? "Corpus passage"}</p>
        </div>
        {source.url && (
          <a href={source.url} target="_blank" rel="noreferrer" aria-label={`Open ${source.label} in a new tab`} className="text-accent hover:underline">
            ↗
          </a>
        )}
      </div>
      <details className="group">
        <summary className="cursor-pointer text-muted">
          <span className="line-clamp-3 block">{source.snippet}</span>
          <span className="ml-1 text-xs text-accent">Expand…</span>
        </summary>
        <span className="mt-2 block whitespace-pre-wrap break-words">{source.snippet}</span>
      </details>
      <p className="mt-2 text-xs text-muted">
        {isWeb ? "web" : "corpus"} · relevance <span className="tabular">{source.relevance_score.toFixed(2)}</span>
        {!source.used && " · considered only"}
        {index === 0 && isWeb && " · fetched today"}
      </p>
    </article>
  );
}
