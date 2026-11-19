import { Moon, Play, Sun } from "lucide-react";
import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { buttonPrimary } from "./components";

const NAV = [
  { to: "/", label: "Results", match: (p: string) => p === "/" || p.startsWith("/runs/") || p.startsWith("/jobs/") },
  { to: "/new", label: "New test", match: (p: string) => p === "/new" },
  { to: "/compare", label: "Compare", match: (p: string) => p === "/compare" },
  { to: "/about", label: "Help", match: (p: string) => p === "/about" },
];

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  const toggle = () => {
    const next = !dark;
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("touchstone-theme", next ? "dark" : "light");
    } catch {
      // storage may be blocked; the toggle still works for this visit
    }
    setDark(next);
  };
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      className="flex size-10 items-center justify-center rounded-lg text-muted transition-colors duration-150 hover:bg-surface-2 hover:text-text"
    >
      {dark ? <Sun aria-hidden className="size-5" /> : <Moon aria-hidden className="size-5" />}
    </button>
  );
}

export function Layout() {
  const { pathname } = useLocation();
  return (
    <div className="min-h-dvh">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:m-2 focus:rounded focus:bg-surface focus:p-2">
        Skip to content
      </a>
      <header className="sticky top-0 z-10 border-b border-line bg-surface">
        <div className="mx-auto flex h-16 max-w-[1120px] items-center gap-4 px-4 sm:px-6">
          <Link to="/" className="text-lg font-semibold tracking-tight text-primary">
            touchstone
          </Link>
          <nav aria-label="Main" className="flex min-w-0 gap-1 overflow-x-auto">
            {NAV.map((item) => {
              const active = item.match(pathname);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  aria-current={active ? "page" : undefined}
                  className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
                    active ? "bg-surface-2 font-semibold text-primary" : "text-muted hover:text-text"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <ThemeToggle />
            <span className="hidden sm:block">
              <Link to="/new" className={buttonPrimary}>
                <Play aria-hidden className="size-4" /> New test
              </Link>
            </span>
          </div>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-[1120px] px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
