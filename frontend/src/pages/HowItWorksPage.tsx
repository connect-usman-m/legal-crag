const LIMITATIONS = [
  "The LLM judge is a stand-in for CRAG's fine-tuned evaluator; calibration is empirical.",
  "15 questions are a portfolio demonstration, not a benchmark.",
  "Web results are labelled and trust-weighted, not verified.",
  "Confidence is a heuristic, not a probability.",
  "Not legal advice. Demo over GDPR + 3 EDPB guidelines.",
];

export default function HowItWorksPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="font-serif text-3xl">How it works</h1>
      <p className="mt-2 text-sm text-muted">A Corrective RAG state machine over a curated legal corpus.</p>

      <section className="mt-8 rounded-card border border-hairline bg-surface p-4" aria-labelledby="graph-title">
        <h2 id="graph-title" className="mb-3 font-serif text-lg">The graph</h2>
        <svg
          viewBox="0 0 900 500"
          className="w-full text-ink"
          role="img"
          aria-label="Retrieve, evaluate, route by decision to passthrough, filter supplement or web correct, then generate, cite and end"
        >
          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,6 L9,3 z" className="fill-muted" />
            </marker>
          </defs>
          <g fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M450 46V70" markerEnd="url(#arrow)" />
            <path d="M450 106V130" markerEnd="url(#arrow)" />
            <path d="M450 166V195H150V230" markerEnd="url(#arrow)" />
            <path d="M450 166V230" markerEnd="url(#arrow)" />
            <path d="M450 166V195H750V230" markerEnd="url(#arrow)" />
            <path d="M150 284V305H450V330" markerEnd="url(#arrow)" />
            <path d="M450 284V330" markerEnd="url(#arrow)" />
            <path d="M750 284V305H450V330" markerEnd="url(#arrow)" />
            <path d="M450 366V390" markerEnd="url(#arrow)" />
            <path d="M450 426V450" markerEnd="url(#arrow)" />
          </g>
          <g fontFamily="IBM Plex Sans, sans-serif" textAnchor="middle">
            <rect x="380" y="10" width="140" height="36" rx="8" className="fill-page stroke-hairline" />
            <text x="450" y="33" fontSize="13" className="fill-ink">Question / START</text>

            <rect x="380" y="70" width="140" height="36" rx="8" className="fill-page stroke-hairline" />
            <text x="450" y="93" fontSize="13" className="fill-ink">retrieve</text>

            <rect x="380" y="130" width="140" height="36" rx="8" className="fill-page stroke-hairline" />
            <text x="450" y="153" fontSize="13" className="fill-ink">evaluate</text>
            <text x="450" y="190" fontSize="11" className="fill-muted">route_after_evaluate</text>

            <rect x="40" y="230" width="220" height="54" rx="8" className="fill-decision-correct-bg stroke-decision-correct-fg" />
            <text x="150" y="250" fontSize="11" className="fill-decision-correct-fg">max ≥ upper</text>
            <text x="150" y="270" fontSize="13" className="fill-decision-correct-fg">CORRECT → passthrough</text>

            <rect x="340" y="230" width="220" height="54" rx="8" className="fill-decision-ambiguous-bg stroke-decision-ambiguous-fg" />
            <text x="450" y="250" fontSize="11" className="fill-decision-ambiguous-fg">lower ≤ max &lt; upper</text>
            <text x="450" y="270" fontSize="13" className="fill-decision-ambiguous-fg">AMBIGUOUS → filter_supplement</text>

            <rect x="640" y="230" width="220" height="54" rx="8" className="fill-decision-incorrect-bg stroke-decision-incorrect-fg" />
            <text x="750" y="250" fontSize="11" className="fill-decision-incorrect-fg">max &lt; lower</text>
            <text x="750" y="270" fontSize="13" className="fill-decision-incorrect-fg">INCORRECT → web_correct</text>

            <rect x="380" y="330" width="140" height="36" rx="8" className="fill-page stroke-hairline" />
            <text x="450" y="353" fontSize="13" className="fill-ink">generate</text>

            <rect x="380" y="390" width="140" height="36" rx="8" className="fill-page stroke-hairline" />
            <text x="450" y="413" fontSize="13" className="fill-ink">cite</text>

            <rect x="380" y="450" width="140" height="36" rx="8" className="fill-page stroke-hairline" />
            <text x="450" y="473" fontSize="13" className="fill-ink">Answer / END</text>
          </g>
        </svg>
      </section>

      <section className="mt-8">
        <h2 className="font-serif text-lg">Thresholds</h2>
        <div className="mt-3 h-10 rounded-card bg-decision-incorrect-bg p-1" aria-label="Lower 0.3, keep 0.5, upper 0.7">
          <div className="flex h-full items-center justify-between text-xs">
            <span className="ml-1">0</span>
            <span>LOWER 0.3</span>
            <span>KEEP 0.5</span>
            <span>UPPER 0.7</span>
            <span className="mr-1">1</span>
          </div>
        </div>
        <p className="mt-2 text-sm text-muted">
          These are the runtime defaults from <code>.env</code>. max ≥ upper routes to corpus passthrough; max &lt; lower routes to web correction; anything between routes to filter and supplement. KEEP removes weak chunks but does not decide the branch. The evaluation run uses the calibrated values recorded in its results config.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="font-serif text-lg">Corpus</h2>
        <ul className="mt-2 list-disc pl-5 text-sm text-muted">
          <li><a className="text-accent hover:underline" href="https://eur-lex.europa.eu/eli/reg/2016/679/oj" target="_blank" rel="noreferrer">GDPR (Regulation 2016/679)</a></li>
          <li>EDPB Guidelines 05/2020 on consent, 9/2022 on breach notification, 01/2022 on access rights</li>
        </ul>
        <p className="mt-2 text-sm text-muted">Excluded on purpose: US state privacy laws, HIPAA, CCPA and enforcement decisions. Those questions exercise the web fallback.</p>
      </section>

      <section className="mt-8">
        <h2 className="font-serif text-lg">Limitations</h2>
        <ul className="mt-2 list-disc pl-5 text-sm text-muted">
          {LIMITATIONS.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </div>
  );
}
