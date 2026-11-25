import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useQueryMutation } from "../api/queries";
import ExampleChips from "../components/query/ExampleChips";
import QuestionInput from "../components/query/QuestionInput";
import ModeToggle from "../components/query/ModeToggle";
import PipelineStepper from "../components/query/PipelineStepper";
import ErrorBanner from "../components/result/ErrorBanner";
import ResultPanel from "../components/result/ResultPanel";
import type { Mode } from "../types/api";

export default function AskPage() {
  const [params, setParams] = useSearchParams();
  const [question, setQuestion] = useState(params.get("q") ?? "");
  const [mode, setMode] = useState<Mode>(params.get("mode") === "naive" ? "naive" : "crag");
  const mutation = useQueryMutation();
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => controller.current?.abort(), []);

  const submit = (nextQuestion = question, nextMode = mode) => {
    if (nextQuestion.trim().length < 3 || nextQuestion.length > 500) return;
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    setParams({ q: nextQuestion, mode: nextMode });
    mutation.mutate({ request: { question: nextQuestion, mode: nextMode }, signal: next.signal });
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="max-w-3xl font-serif text-3xl leading-tight text-balance sm:text-4xl">
        Ask a question about EU data-protection law
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Each answer shows the retrieval decision and the scores behind it.
      </p>

      <div className="mt-8 space-y-4">
        <QuestionInput value={question} onChange={setQuestion} onSubmit={submit} loading={mutation.isPending} />
        <ModeToggle
          value={mode}
          onChange={(next) => {
            setMode(next);
            setParams({ q: question, mode: next });
          }}
        />
        <ExampleChips
          onSelect={(example) => {
            setQuestion(example);
            submit(example, mode);
          }}
        />
      </div>

      <div className="mt-8">
        <PipelineStepper loading={mutation.isPending} decision={mutation.data?.retrieval_decision ?? null} />
      </div>

      {mutation.isPending && (
        <div className="mt-8 space-y-3" aria-label="Loading answer">
          <div className="h-5 w-2/3 animate-pulse rounded bg-hairline" />
          <div className="h-5 w-3/4 animate-pulse rounded bg-hairline" />
          <div className="h-5 w-1/2 animate-pulse rounded bg-hairline" />
        </div>
      )}
      {mutation.isError && <ErrorBanner error={mutation.error} onRetry={() => submit()} />}
      {mutation.data && <ResultPanel result={mutation.data} />}
    </div>
  );
}
