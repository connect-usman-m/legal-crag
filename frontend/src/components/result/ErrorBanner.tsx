import { useEffect, useState } from "react";

import { ApiError } from "../../api/client";

type Props = { error: unknown; onRetry: () => void };

export default function ErrorBanner({ error, onRetry }: Props) {
  const apiError = error instanceof ApiError ? error : null;
  const [seconds, setSeconds] = useState(apiError?.retryAfter ?? 0);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = window.setInterval(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [seconds]);

  const message = apiError?.message ?? "The request failed. Retry or reload the page.";
  const retry = apiError?.code === "rate_limited" ? `Retry in ${seconds}s` : "Retry";

  return (
    <div role="alert" className="mt-6 rounded-card border border-decision-ambiguous-fg bg-decision-ambiguous-bg p-4 text-sm">
      <p className="font-medium">{message}</p>
      {apiError && <p className="mt-1 text-xs text-muted">Request {apiError.requestId}</p>}
      <button
        type="button"
        onClick={onRetry}
        disabled={seconds > 0}
        className="mt-3 rounded-card border border-accent px-3 py-1 text-accent hover:bg-surface disabled:opacity-50"
      >
        {retry}
      </button>
    </div>
  );
}
