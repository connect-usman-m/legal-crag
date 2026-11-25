type Props = { warnings: string[]; citationCoverage: number };

const NAMES: Record<string, string> = {
  web_search_failed: "Web search failed",
  low_citation_coverage: "Some statements may lack citations",
  no_corpus_chunks_above_keep: "No corpus chunks above keep",
};

export default function WarningChips({ warnings, citationCoverage }: Props) {
  const all = [...warnings];
  if (citationCoverage < 0.8 && !all.includes("low_citation_coverage")) all.push("low_citation_coverage");
  if (all.length === 0) return null;
  return (
    <ul className="mt-4 flex flex-wrap gap-2 text-xs" aria-label="Warnings">
      {all.map((warning) => (
        <li key={warning} className="rounded-full border border-decision-ambiguous-fg px-2 py-1 text-decision-ambiguous-fg">
          {NAMES[warning] ?? warning}
        </li>
      ))}
    </ul>
  );
}
