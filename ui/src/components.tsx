import { AlertTriangle, Info, Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { pct } from "./lib";

/*
 * Spacing scale used everywhere: 8 / 16 / 24 / 32 px (Tailwind 2 / 4 / 6 / 8).
 * Cards: 24px padding, 16px radius. Sections: 24px apart. Buttons: 40px tall.
 */

export const buttonPrimary =
  "inline-flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-accent px-5 text-sm font-semibold text-on-accent shadow-sm transition-colors duration-150 hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50";
export const buttonSecondary =
  "inline-flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg border border-line-strong bg-surface px-4 text-sm font-medium text-text transition-colors duration-150 hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50";
export const inputClass =
  "h-10 rounded-lg border border-line-strong bg-surface px-3 text-sm text-text placeholder:text-muted";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-line bg-surface p-6 ${className}`}>{children}</section>;
}

export function CardTitle({ children, hint }: { children: ReactNode; hint?: ReactNode }) {
  return (
    <div className="mb-4">
      <h2 className="text-base font-semibold text-primary">{children}</h2>
      {hint && <p className="mt-1 text-sm text-muted">{hint}</p>}
    </div>
  );
}

export function PageTitle({ title, sub, action }: { title: string; sub?: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold text-primary">{title}</h1>
        {sub && <p className="mt-1 text-sm text-muted">{sub}</p>}
      </div>
      {action}
    </div>
  );
}

/** A plain-language explanation box. Always visible, never hover-only. */
export function InfoBox({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="flex gap-3 rounded-xl bg-info-bg p-4 text-sm text-info">
      <Info aria-hidden className="mt-0.5 size-4 shrink-0" />
      <div className="space-y-1">
        {title && <p className="font-semibold">{title}</p>}
        <div>{children}</div>
      </div>
    </div>
  );
}

/** Small helper line under a form field or heading. */
export function Hint({ children }: { children: ReactNode }) {
  return <p className="mt-1.5 text-xs leading-relaxed text-muted">{children}</p>;
}

export function UnreviewedBanner() {
  return (
    <div role="alert" className="mb-6 flex items-start gap-3 rounded-xl bg-warn-bg p-4 text-sm text-warn">
      <AlertTriangle aria-hidden className="mt-0.5 size-4 shrink-0" />
      <p>
        <span className="font-semibold">Practice run with draft questions.</span> These questions have not yet been
        checked by two reviewers, so treat the numbers as a trial only and do not publish them.
      </p>
    </div>
  );
}

export function UnreviewedBadge() {
  return (
    <span className="ml-2 inline-block rounded-md bg-warn-bg px-2 py-0.5 text-xs font-medium text-warn">
      draft questions
    </span>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div role="alert" className="whitespace-pre-wrap rounded-xl border border-danger/40 bg-surface p-4 text-sm text-danger">
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

/** Horizontal bar with a visible value label (never color alone). */
export function ScoreBar({ value, color = "var(--series-1)", label }: { value: number; color?: string; label?: string }) {
  const width = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="flex items-center gap-3" title={label ? `${label}: ${pct(value)}` : pct(value)}>
      <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-2" aria-hidden>
        <div className="h-full rounded-full transition-[width] duration-300" style={{ width: `${width}%`, background: color }} />
      </div>
      <span className="tabular w-14 text-right text-sm font-medium">{pct(value)}</span>
    </div>
  );
}

export function Meta({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="text-xs font-medium text-muted">{label}</div>
      <div className="mt-1 break-words text-sm">{children}</div>
    </div>
  );
}

/** Numbered step card, used for "how it works" rows. */
export function StepCard({ n, title, children }: { n: number; title: string; children: ReactNode }) {
  return (
    <div className="flex h-full gap-4 rounded-2xl border border-line bg-surface p-5">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-accent text-sm font-semibold text-on-accent">
        {n}
      </span>
      <div>
        <h3 className="text-sm font-semibold text-primary">{title}</h3>
        <p className="mt-1 text-sm text-muted">{children}</p>
      </div>
    </div>
  );
}

export const GLOSSARY: { term: string; meaning: string }[] = [
  { term: "Score", meaning: "Share of questions the model answered correctly. 100% means every question was right." },
  { term: "n", meaning: "How many questions were asked. n=2 means only 2 questions, so the score is a rough trial." },
  { term: "Mean score", meaning: "The average of the task scores, so every task counts equally." },
  { term: "Unparsed", meaning: "The model did not give a clear answer (for example it said \"A or B\"), so it counts as wrong." },
  { term: "Draft questions", meaning: "Questions not yet approved by two reviewers. Fine for practice, not for publishing." },
  { term: "Model id reported", meaning: "The exact model the provider says it used. It can differ from the name you picked." },
];

export function Glossary() {
  return (
    <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
      {GLOSSARY.map((g) => (
        <div key={g.term}>
          <dt className="font-semibold text-primary">{g.term}</dt>
          <dd className="text-muted">{g.meaning}</dd>
        </div>
      ))}
    </dl>
  );
}
