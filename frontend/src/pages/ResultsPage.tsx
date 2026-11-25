import { Link } from "react-router-dom";

import { useEvalResults } from "../api/queries";
import CategoryChart from "../components/eval/CategoryChart";
import ResultsTable from "../components/eval/ResultsTable";
import SummaryCards from "../components/eval/SummaryCards";

export default function ResultsPage() {
  const results = useEvalResults();

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="font-serif text-3xl">Evaluation results</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Frozen 15-question test set, both modes, with manual review applied last.
      </p>
      {results.isPending && <p role="status" className="mt-6 text-sm text-muted">Loading results…</p>}
      {results.isError && <p role="alert" className="mt-6 text-sm">Could not load results. Retry by reloading the page.</p>}
      {results.data && (
        <>
          <div className="mt-6"><SummaryCards run={results.data} /></div>
          <CategoryChart run={results.data} />
          <ResultsTable records={results.data.records} />
          <p className="mt-6 text-xs text-muted">
            Run {results.data.run_id} · {results.data.split} · trace links appear when LangSmith is configured.{" "}
            <Link to="/how-it-works" className="text-accent hover:underline">Read the method →</Link>
          </p>
        </>
      )}
    </div>
  );
}
