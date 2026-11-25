import { Fragment, useState } from "react";
import { Link } from "react-router-dom";

import { decisionToken } from "../../lib/decisionTokens";
import type { EvalRecord } from "../../types/api";

type SortKey = "qid" | "category";

const MARKS: Record<string, string> = {
  correct: "✓",
  partial: "~",
  incorrect: "✗",
  abstained: "⊘",
};

export default function ResultsTable({ records }: { records: EvalRecord[] }) {
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState<SortKey>("qid");
  const [expanded, setExpanded] = useState<string | null>(null);

  const crag = records.filter((record) => record.mode === "crag");
  const naiveByQid = new Map(records.filter((record) => record.mode === "naive").map((record) => [record.qid, record]));
  const filtered = crag
    .filter((record) => category === "all" || record.category === category)
    .slice()
    .sort((left: EvalRecord, right: EvalRecord) => left[sort].localeCompare(right[sort]));

  return (
    <section className="mt-8">
      <div className="mb-3 flex flex-wrap items-center gap-3 text-sm">
        <label htmlFor="category-filter">Category</label>
        <select
          id="category-filter"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          className="rounded-card border border-hairline bg-surface p-1"
        >
          <option value="all">All</option>
          <option value="covered">Covered</option>
          <option value="not_covered">Not covered</option>
          <option value="ambiguous">Ambiguous</option>
        </select>
        <label htmlFor="sort">Sort by</label>
        <select
          id="sort"
          value={sort}
          onChange={(event) => setSort(event.target.value as SortKey)}
          className="rounded-card border border-hairline bg-surface p-1"
        >
          <option value="qid">Question ID</option>
          <option value="category">Category</option>
        </select>
      </div>
      <div className="overflow-x-auto rounded-card border border-hairline bg-surface">
        <table className="w-full min-w-[820px] text-left text-sm">
          <caption className="sr-only">Evaluation results by question</caption>
          <thead className="border-b border-hairline text-xs text-muted">
            <tr>
              <th scope="col" className="p-3">#</th>
              <th scope="col" className="p-3">Category</th>
              <th scope="col" className="p-3">Expected</th>
              <th scope="col" className="p-3">CRAG branch</th>
              <th scope="col" className="p-3">Naive</th>
              <th scope="col" className="p-3">CRAG</th>
              <th scope="col" className="p-3">Traces</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((record) => {
              const naive = naiveByQid.get(record.qid);
              const token = decisionToken(
                record.actual_branch === "CORRECT" || record.actual_branch === "AMBIGUOUS" || record.actual_branch === "INCORRECT"
                  ? record.actual_branch
                  : null,
              );
              return (
                <Fragment key={record.qid}>
                  <tr className="border-b border-hairline">
                    <th scope="row" className="p-3 font-mono font-normal">{record.qid}</th>
                    <td className="p-3">{record.category.replace("_", " ")}</td>
                    <td className="p-3">{record.expected_branch ?? "—"}</td>
                    <td className="p-3">
                      <span className={`rounded-full px-2 py-1 text-xs ${token.bgToken} ${token.fgToken}`}>
                        {token.label} {record.branch_correct ? "✓" : "✗"}
                      </span>
                    </td>
                    <td className="p-3 tabular">{naive ? MARKS[naive.grade] ?? naive.grade : "—"}</td>
                    <td className="p-3 tabular">{MARKS[record.grade] ?? record.grade}</td>
                    <td className="p-3">
                      <div className="flex gap-2 text-xs text-accent">
                        {naive?.trace_url && <a href={naive.trace_url} target="_blank" rel="noreferrer">naive ↗</a>}
                        {record.trace_url && <a href={record.trace_url} target="_blank" rel="noreferrer">crag ↗</a>}
                        <Link to={`/compare?q=${encodeURIComponent(record.answer)}`}>re-run</Link>
                      </div>
                    </td>
                    <td className="p-3">
                      <button
                        type="button"
                        className="text-accent hover:underline"
                        aria-expanded={expanded === record.qid}
                        aria-controls={`eval-row-${record.qid}`}
                        onClick={() => setExpanded(expanded === record.qid ? null : record.qid)}
                      >
                        {expanded === record.qid ? "Hide" : "Answers"}
                      </button>
                    </td>
                  </tr>
                  {expanded === record.qid && (
                    <tr id={`eval-row-${record.qid}`} className="border-b border-hairline bg-page">
                      <td colSpan={8} className="p-4 text-xs">
                        <p><strong>Naive:</strong> {naive?.answer ?? "—"}</p>
                        <p className="mt-2"><strong>CRAG:</strong> {record.answer}</p>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
