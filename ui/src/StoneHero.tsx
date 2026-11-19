import { Sparkles, TrendingDown, TrendingUp } from "lucide-react";
import type { RunResult, Sample } from "./api";
import { ScoreBar, useCountUp } from "./components";
import { pct } from "./lib";

/** Pick one failed item to show: prefer a parsed-but-wrong answer over an unparsed one. */
function toughestItem(run: RunResult): { task: string; s: Sample } | null {
  const misses = run.tasks.flatMap((t) => t.samples.filter((s) => s.score < 1).map((s) => ({ task: t.task, s })));
  if (misses.length === 0) return null;
  return misses.find((m) => !m.s.unparsed && m.s.output.trim()) ?? misses[0];
}

function short(text: string, max = 90) {
  const one = text.replace(/\s+/g, " ").trim();
  return one.length > max ? `${one.slice(0, max)}…` : one;
}

/**
 * The touchstone: a dark stone panel where each task score is a gold streak.
 * Highlights describe this model's own results only; they never rank models.
 */
export function StoneHero({ run }: { run: RunResult }) {
  const tasks = run.tasks;
  const mean = tasks.length ? tasks.reduce((a, t) => a + t.score, 0) / tasks.length : 0;
  const n = tasks.reduce((a, t) => a + t.n, 0);
  const shown = useCountUp(mean);
  const top = Math.max(...tasks.map((t) => t.score));
  const bottom = Math.min(...tasks.map((t) => t.score));
  const strongest = tasks.filter((t) => t.score === top);
  const weakest = tasks.filter((t) => t.score === bottom);
  const tough = toughestItem(run);

  return (
    <section aria-label="Results summary" className="mb-4 overflow-hidden rounded-2xl bg-stone text-on-stone">
      <div className="grid gap-6 p-5 md:grid-cols-[240px_minmax(0,1fr)] md:p-6">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-on-stone-muted">Mean score</div>
          <div className="tabular mt-1 text-6xl font-semibold leading-none text-gold-bright" aria-live="polite">
            {pct(shown)}
          </div>
          <div className="mt-2 text-sm text-on-stone-muted">
            average of {tasks.length} task score{tasks.length === 1 ? "" : "s"} · n={n}
          </div>
        </div>
        <div className="space-y-2.5">
          {tasks.map((t, i) => (
            <div key={t.task} className="grid grid-cols-1 gap-1 sm:grid-cols-[230px_minmax(0,1fr)] sm:items-center">
              <div className="font-mono text-[13px] break-all">
                {t.task}
                <span className="ml-2 text-xs text-on-stone-muted">n={t.n}</span>
              </div>
              <ScoreBar
                value={t.score}
                label={t.task}
                delayMs={150 + i * 110}
                color="linear-gradient(90deg, var(--gold), var(--gold-bright))"
                track="bg-stone-2"
              />
            </div>
          ))}
        </div>
      </div>

      {tasks.length > 1 && top !== bottom && (
        <div className="grid gap-px bg-stone-2 sm:grid-cols-3">
          <Highlight icon={<TrendingUp aria-hidden className="size-4" />} label="Strongest task">
            <TaskList tasks={strongest.map((t) => t.task)} /> · {pct(top)}
          </Highlight>
          <Highlight icon={<TrendingDown aria-hidden className="size-4" />} label="Hardest task">
            <TaskList tasks={weakest.map((t) => t.task)} /> · {pct(bottom)}
          </Highlight>
          <Highlight icon={<Sparkles aria-hidden className="size-4" />} label="Toughest item">
            {tough ? (
              <>
                <span className="block truncate">“{short(tough.s.output) || "(empty reply)"}”</span>
                <span className="text-on-stone-muted">
                  expected {short(Array.isArray(tough.s.expected) ? tough.s.expected[0] : tough.s.expected, 40)}
                </span>
              </>
            ) : (
              "Every item scored full marks."
            )}
          </Highlight>
        </div>
      )}
    </section>
  );
}

function Highlight({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div className="bg-stone px-5 py-3 text-sm">
      <div className="mb-1 flex items-center gap-1.5 text-xs text-gold-bright">
        {icon} {label}
      </div>
      <div className="min-w-0">{children}</div>
    </div>
  );
}

/** One task name, or "N tasks tied" so a tie is never shown as a single winner. */
function TaskList({ tasks }: { tasks: string[] }) {
  if (tasks.length === 1) return <span className="font-mono text-[13px]">{tasks[0]}</span>;
  return <span title={tasks.join(", ")}>{tasks.length} tasks tied</span>;
}
