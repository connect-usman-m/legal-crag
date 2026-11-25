export type Decision = "CORRECT" | "AMBIGUOUS" | "INCORRECT" | null;

type DecisionToken = {
  label: string;
  icon: string;
  fgToken: string;
  bgToken: string;
  tooltip: string;
};

export function decisionToken(decision: Decision): DecisionToken {
  switch (decision) {
    case "CORRECT":
      return {
        label: "Answered from corpus",
        icon: "✓",
        fgToken: "text-decision-correct-fg",
        bgToken: "bg-decision-correct-bg",
        tooltip: "The judge kept corpus passages. The answer uses corpus only.",
      };
    case "AMBIGUOUS":
      return {
        label: "Corpus + web",
        icon: "◐",
        fgToken: "text-decision-ambiguous-fg",
        bgToken: "bg-decision-ambiguous-bg",
        tooltip: "The judge found partial matches, dropped weak passages, and added web sources.",
      };
    case "INCORRECT":
      return {
        label: "Web fallback",
        icon: "↻",
        fgToken: "text-decision-incorrect-fg",
        bgToken: "bg-decision-incorrect-bg",
        tooltip: "No corpus passage matched. The judge discarded them; this answer uses web sources.",
      };
    default:
      return {
        label: "Naive RAG (no gate)",
        icon: "—",
        fgToken: "text-decision-naive-fg",
        bgToken: "bg-decision-naive-bg",
        tooltip: "The baseline retrieves from FAISS and generates an answer without an evidence gate.",
      };
  }
}

export function isAbstained(abstained: boolean, answer: string): boolean {
  return abstained || /^NOT ENOUGH EVIDENCE/i.test(answer.trim());
}
