const EXAMPLES = [
  { category: "Covered", question: "Within how many hours must a breach be notified?" },
  { category: "Covered", question: "What are the lawful bases for processing personal data?" },
  { category: "Not covered", question: "What are the penalties for violating the CCPA?" },
  { category: "Not covered", question: "What did Schrems II decide about Privacy Shield?" },
  { category: "Ambiguous", question: "How much was Meta fined by the Irish DPC in 2023?" },
  { category: "Ambiguous", question: "Can personal data be transferred to the US today?" },
];

type Props = { onSelect: (question: string) => void };

export default function ExampleChips({ onSelect }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <span className="text-muted">Try:</span>
      {EXAMPLES.map((example) => (
        <button
          key={example.question}
          type="button"
          onClick={() => onSelect(example.question)}
          className="rounded-full border border-hairline bg-surface px-3 py-1 text-left text-muted hover:border-accent hover:text-ink"
          aria-label={`${example.category} example: ${example.question}`}
        >
          <span className="font-medium text-ink">{example.category}</span> · {example.question}
        </button>
      ))}
    </div>
  );
}
