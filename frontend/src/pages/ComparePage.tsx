import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useCompareMutation } from "../api/queries";
import QuestionInput from "../components/query/QuestionInput";
import CompareColumns from "../components/compare/CompareColumns";
import DiffHint from "../components/compare/DiffHint";
import ErrorBanner from "../components/result/ErrorBanner";

export default function ComparePage() {
  const [params, setParams] = useSearchParams();
  const [question, setQuestion] = useState(params.get("q") ?? "");
  const mutation = useCompareMutation();
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => controller.current?.abort(), []);

  const submit = (next = question) => {
    if (next.trim().length < 3 || next.length > 500) return;
    controller.current?.abort();
    const nextController = new AbortController();
    controller.current = nextController;
    setParams({ q: next });
    mutation.mutate({ question: next, signal: nextController.signal });
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="font-serif text-3xl">Compare Naive RAG with CRAG</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">The API runs both pipelines on one question.</p>
      <div className="mt-6">
        <QuestionInput value={question} onChange={setQuestion} onSubmit={() => submit()} loading={mutation.isPending} />
      </div>
      {mutation.isPending && <p role="status" className="mt-6 text-sm text-muted">Running both pipelines…</p>}
      {mutation.isError && <ErrorBanner error={mutation.error} onRetry={() => submit()} />}
      {mutation.data && (
        <>
          <DiffHint payload={mutation.data} />
          <CompareColumns naive={mutation.data.naive} crag={mutation.data.crag} />
        </>
      )}
      {!mutation.data && !mutation.isPending && (
        <p className="mt-8 rounded-card border border-dashed border-hairline p-6 text-sm text-muted">
          Enter a question to see the difference. Try the CCPA penalties example from the Ask page.
        </p>
      )}
    </div>
  );
}
