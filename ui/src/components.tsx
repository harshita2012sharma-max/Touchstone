import { AlertTriangle, Loader2 } from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";
import { pct } from "./lib";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-line bg-surface p-4 ${className}`}>{children}</section>
  );
}

export function PageTitle({ title, sub, action }: { title: string; sub?: string; action?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold text-primary">{title}</h1>
        {sub && <p className="mt-1 text-sm text-muted">{sub}</p>}
      </div>
      {action}
    </div>
  );
}

export function UnreviewedBanner() {
  return (
    <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg bg-warn-bg px-4 py-3 text-sm font-medium text-warn">
      <AlertTriangle aria-hidden className="mt-0.5 size-4 shrink-0" />
      <span>Unreviewed data. These items were not checked by two reviewers. Do not publish these numbers.</span>
    </div>
  );
}

export function UnreviewedBadge() {
  return (
    <span className="ml-2 inline-block rounded bg-warn-bg px-1.5 py-0.5 text-xs font-medium text-warn">
      unreviewed
    </span>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-lg border border-danger/40 px-4 py-3 text-sm text-danger whitespace-pre-wrap">
      {message}
    </div>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <p className="flex items-center gap-2 text-sm text-muted" aria-live="polite">
      <Loader2 aria-hidden className="size-4 animate-spin" /> {label}…
    </p>
  );
}

/** Horizontal "gold streak" bar with a visible value label (never color alone). */
export function ScoreBar({
  value,
  color = "var(--gold)",
  label,
  delayMs = 0,
  track = "bg-surface-2",
  valueClass = "",
}: {
  value: number;
  color?: string;
  label?: string;
  delayMs?: number;
  track?: string;
  valueClass?: string;
}) {
  const width = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="flex items-center gap-2" title={label ? `${label}: ${pct(value)}` : pct(value)}>
      <div className={`h-3 flex-1 rounded-r-[4px] ${track}`} aria-hidden>
        <div
          className="streak h-full rounded-r-[4px]"
          style={{ width: `${width}%`, background: color, animationDelay: `${delayMs}ms` }}
        />
      </div>
      <span className={`tabular w-14 text-right text-sm ${valueClass}`}>{pct(value)}</span>
    </div>
  );
}

/** Animate a number from 0 to `value` once (instant when reduced motion is on). */
export function useCountUp(value: number, durationMs = 900) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(value);
      return;
    }
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      setShown(value * (1 - Math.pow(1 - t, 3)));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, durationMs]);
  return shown;
}

export function Meta({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-lg bg-surface-2 px-3 py-2">
      <div className="text-xs text-muted">{label}</div>
      <div className="text-sm break-words">{children}</div>
    </div>
  );
}

export const buttonPrimary =
  "inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-on-accent transition-opacity duration-150 hover:opacity-90 disabled:opacity-50";
export const buttonSecondary =
  "inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm text-text transition-colors duration-150 hover:bg-surface-2";
export const inputClass =
  "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-text";
