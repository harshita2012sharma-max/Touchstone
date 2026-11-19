import { useEffect, useState } from "react";

/** Format a 0-1 score as a percentage with one decimal. */
export function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

/** Local date and time, e.g. "19 Nov 2026, 11:44". */
export function when(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)"] as const;
export const MAX_COMPARE = SERIES.length;

/** Small fetch hook: { data, error, loading } with a reload function. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    setError(null);
    load()
      .then((d) => alive && setData(d))
      .catch((e: unknown) => alive && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { data, error, loading: data === null && error === null, reload: () => setTick((t) => t + 1) };
}
