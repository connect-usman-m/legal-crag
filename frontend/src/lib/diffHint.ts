type HintInput = {
  naive: { answer: string; sources: { label: string }[] };
  crag: {
    answer: string;
    sources: { label: string }[];
    retrieval_decision: "CORRECT" | "AMBIGUOUS" | "INCORRECT" | null;
    chunk_scores: { label: string; score: number | null; kept: boolean }[] | null;
  };
};

export function buildDiffHint(payload: HintInput): string {
  const scores = payload.crag.chunk_scores ?? [];
  const max = Math.max(
    0,
    ...scores.map((score) => score.score ?? 0),
  );

  if (payload.crag.retrieval_decision === "INCORRECT") {
    const naiveLabel = payload.naive.sources[0]?.label;
    const rejected = naiveLabel ? scores.find((score) => score.label === naiveLabel && !score.kept) : undefined;
    const detail = rejected
      ? `Naive cited ${rejected.label}; CRAG scored it ${(rejected.score ?? 0).toFixed(2)} and used web sources.`
      : `No corpus passage was relevant (top ${max.toFixed(2)}); CRAG used web sources.`;
    return detail;
  }

  if (payload.crag.retrieval_decision === "AMBIGUOUS") {
    return `The judge found only partial corpus matches (top ${max.toFixed(2)}); CRAG combined kept chunks with web sources.`;
  }

  if (payload.crag.retrieval_decision === "CORRECT") {
    return `The judge kept corpus passages (top ${max.toFixed(2)}). Both modes answered from corpus.`;
  }

  return "Both modes answered without an evidence gate.";
}
