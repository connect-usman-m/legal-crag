import type { Mode } from "../../types/api";

type Props = { value: Mode; onChange: (mode: Mode) => void };

export default function ModeToggle({ value, onChange }: Props) {
  return (
    <fieldset className="flex items-center gap-4 text-sm">
      <legend className="sr-only">Retrieval mode</legend>
      <label className="flex cursor-pointer items-center gap-2">
        <input
          type="radio"
          name="mode"
          value="crag"
          checked={value === "crag"}
          onChange={() => onChange("crag")}
          className="accent-accent"
        />
        CRAG
      </label>
      <label className="flex cursor-pointer items-center gap-2">
        <input
          type="radio"
          name="mode"
          value="naive"
          checked={value === "naive"}
          onChange={() => onChange("naive")}
          className="accent-accent"
        />
        Naive
      </label>
    </fieldset>
  );
}
