type Props = { sourceId: string; label: string; onSelect: (id: string) => void };

export default function CitationChip({ sourceId, label, onSelect }: Props) {
  return (
    <button
      type="button"
      onClick={() => onSelect(sourceId)}
      aria-label={`Source ${sourceId.replace("S", "")}: ${label}`}
      className="mx-0.5 rounded-full border border-hairline bg-surface px-1.5 py-0.5 align-super font-sans text-[0.6em] font-semibold text-accent hover:border-accent"
    >
      {sourceId}
    </button>
  );
}
