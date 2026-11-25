import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";

const NAV = [
  { to: "/", label: "Ask" },
  { to: "/compare", label: "Compare" },
  { to: "/eval", label: "Results" },
  { to: "/how-it-works", label: "How it works" },
];

export default function TopBar() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", dark ? "#121316" : "#FAFAF7");
  }, [dark]);

  return (
    <header className="border-b border-hairline">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-3 sm:px-6">
        <Link to="/" className="font-serif text-xl font-semibold tracking-tight text-ink hover:text-accent">
          LexGate
        </Link>
        <nav aria-label="Main navigation" className="order-3 w-full sm:order-none sm:w-auto sm:flex-1">
          <ul className="flex flex-wrap gap-4 text-sm">
            {NAV.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `border-b-2 pb-0.5 hover:text-accent ${
                      isActive ? "border-accent text-ink" : "border-transparent text-muted"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <button
            type="button"
            className="rounded-full border border-hairline px-3 py-1 text-sm text-muted hover:text-ink"
            aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
            aria-pressed={dark}
            onClick={() => setDark((value) => !value)}
          >
            {dark ? "☀ Light" : "◐ Dark"}
          </button>
          <a
            href="https://github.com/connect-usman-m/legal-crag"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-muted hover:text-accent"
          >
            GitHub
          </a>
        </div>
      </div>
    </header>
  );
}
