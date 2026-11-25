export type AnswerPart =
  | { kind: "text"; text: string }
  | { kind: "citation"; text: string; sourceId: string };

const CITATION = /\[S([1-9]\d*)\]/g;

export function splitCitations(answer: string): AnswerPart[] {
  const parts: AnswerPart[] = [];
  let cursor = 0;
  for (const match of answer.matchAll(CITATION)) {
    const start = match.index ?? 0;
    if (start > cursor) {
      parts.push({ kind: "text", text: answer.slice(cursor, start) });
    }
    parts.push({ kind: "citation", text: match[0], sourceId: `S${match[1]}` });
    cursor = start + match[0].length;
  }
  if (cursor < answer.length) {
    parts.push({ kind: "text", text: answer.slice(cursor) });
  }
  return parts;
}
