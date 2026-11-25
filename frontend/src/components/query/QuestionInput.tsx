import { useEffect, useRef } from "react";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
};

export default function QuestionInput({ value, onChange, onSubmit, loading }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 220)}px`;
  }, [value]);

  const invalid = value.trim().length < 3 || value.length > 500;

  return (
    <div className="w-full">
      <label htmlFor="question" className="mb-2 block text-sm font-medium text-muted">
        Question
      </label>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <textarea
          id="question"
          ref={ref}
          name="question"
          rows={2}
          maxLength={500}
          value={value}
          autoComplete="off"
          placeholder="Ask about GDPR, e.g. When must a DPO be appointed?…"
          aria-describedby="question-help"
          aria-invalid={invalid}
          className="min-h-20 w-full flex-1 resize-none rounded-card border border-hairline bg-surface p-3 text-base text-ink placeholder:text-muted focus-visible:border-accent"
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              if (!invalid && !loading) onSubmit();
            }
          }}
        />
        <button
          type="button"
          disabled={invalid || loading}
          onClick={() => onSubmit()}
          className="shrink-0 rounded-card bg-accent px-5 py-3 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Asking…" : "Ask →"}
        </button>
      </div>
      <p id="question-help" className="mt-1 flex justify-between text-xs text-muted">
        <span>{invalid && value.length > 0 ? "Use between 3 and 500 characters." : "Enter to ask · Shift+Enter for a new line"}</span>
        <span className="tabular">{value.length}/500</span>
      </p>
    </div>
  );
}
