import { decisionToken } from "../../lib/decisionTokens";
import type { Decision } from "../../types/api";

type Props = { decision: Decision; reason: string | null; maxScore: number | null };

export default function DecisionBadge({ decision, reason, maxScore }: Props) {
  const token = decisionToken(decision);
  const tooltip = `${token.tooltip}${maxScore === null ? "" : ` Top score ${maxScore.toFixed(2)}.`}`;
  return (
    <span
      title={tooltip}
      aria-label={`${token.label}. ${tooltip}`}
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${token.bgToken} ${token.fgToken}`}
    >
      <span aria-hidden="true">{token.icon}</span>
      {token.label}
    </span>
  );
}
