import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        page: "var(--page)",
        surface: "var(--surface)",
        ink: "var(--ink)",
        muted: "var(--muted)",
        hairline: "var(--hairline)",
        accent: "var(--accent)",
        "decision-correct-fg": "var(--decision-correct-fg)",
        "decision-correct-bg": "var(--decision-correct-bg)",
        "decision-ambiguous-fg": "var(--decision-ambiguous-fg)",
        "decision-ambiguous-bg": "var(--decision-ambiguous-bg)",
        "decision-incorrect-fg": "var(--decision-incorrect-fg)",
        "decision-incorrect-bg": "var(--decision-incorrect-bg)",
        "decision-naive-fg": "var(--decision-naive-fg)",
        "decision-naive-bg": "var(--decision-naive-bg)",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        serif: ["Source Serif 4", "Georgia", "serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "8px",
      },
    },
  },
} satisfies Config;
