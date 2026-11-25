import CitationChip from "./CitationChip";
import { splitCitations } from "../../lib/formatCitation";

type Props = { answer: string; sources: { id: string; label: string }[]; onSelect: (id: string) => void };

export default function AnswerBody({ answer, sources, onSelect }: Props) {
  const labels = new Map(sources.map((source) => [source.id, source.label]));
  return (
    <p className="prose-answer">
      {splitCitations(answer).map((part, index) =>
        part.kind === "citation" ? (
          <CitationChip
            key={`${part.sourceId}-${index}`}
            sourceId={part.sourceId}
            label={labels.get(part.sourceId) ?? part.sourceId}
            onSelect={onSelect}
          />
        ) : (
          <span key={index}>{part.text}</span>
        ),
      )}
    </p>
  );
}
