import type { RunResult, Sample } from "./api";
import { Card, ScoreBar } from "./components";
import { pct, plainRules, taskLabel } from "./lib";

/** Pick one failed item to show: prefer a clear wrong answer over an unparsed one. */
function hardestItem(run: RunResult): { task: string; s: Sample } | null {
  const misses = run.tasks.flatMap((t) => t.samples.filter((s) => s.score < 1).map((s) => ({ task: t.task, s })));
  if (misses.length === 0) return null;
  return misses.find((m) => !m.s.unparsed && m.s.output.trim()) ?? misses[0];
}

function short(text: string, max = 90) {
  const one = text.replace(/\s+/g, " ").trim();
  return one.length > max ? `${one.slice(0, max)}…` : one;
}

function names(tasks: string[]) {
  return tasks.length === 1 ? taskLabel(tasks[0]) : `${tasks.length} topics tied`;
}

/**
 * Results summary: the overall score, one bar per task, and three plain facts
 * about this model's own results. Highlights never rank models, and ties are
 * shown as ties.
 */
export function StoneHero({ run }: { run: RunResult }) {
  const tasks = run.tasks;
  const mean = tasks.length ? tasks.reduce((a, t) => a + t.score, 0) / tasks.length : 0;
  const n = tasks.reduce((a, t) => a + t.n, 0);
  const correct = tasks.reduce((a, t) => a + t.samples.filter((s) => s.score >= 1).length, 0);
  const top = Math.max(...tasks.map((t) => t.score));
  const bottom = Math.min(...tasks.map((t) => t.score));
  const best = tasks.filter((t) => t.score === top).map((t) => t.task);
  const worst = tasks.filter((t) => t.score === bottom).map((t) => t.task);
  const miss = hardestItem(run);

  return (
    <div className="mb-6 grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
      <Card className="flex flex-col justify-center">
        <p className="text-sm font-medium text-muted">Overall score</p>
        <p className="tabular mt-2 text-5xl font-semibold text-primary">{pct(mean)}</p>
        <p className="mt-3 text-sm text-muted">
          About {correct} of {n} questions fully correct, across {tasks.length} topic{tasks.length === 1 ? "" : "s"}.
        </p>
      </Card>

      <Card>
        <h2 className="mb-1 text-base font-semibold text-primary">Score for each topic</h2>
        <p className="mb-5 text-sm text-muted">Longer bar = more questions answered correctly. n = number of questions.</p>
        <div className="space-y-4">
          {tasks.map((t) => (
            <div key={t.task} className="grid grid-cols-1 gap-1 sm:grid-cols-[240px_minmax(0,1fr)] sm:items-center sm:gap-4">
              <div className="text-sm">
                <span className="font-medium">{taskLabel(t.task)}</span>
                <span className="ml-2 text-xs text-muted">n={t.n}</span>
              </div>
              <ScoreBar value={t.score} label={t.task} />
            </div>
          ))}
        </div>
      </Card>

      {tasks.length > 1 && top !== bottom && (
        <div className="grid gap-6 sm:grid-cols-3 lg:col-span-2">
          <Fact label="Did best on">
            <span className="font-medium">{names(best)}</span> · {pct(top)}
          </Fact>
          <Fact label="Found hardest">
            <span className="font-medium">{names(worst)}</span> · {pct(bottom)}
          </Fact>
          <Fact label="Example of a mistake">
            {miss ? (
              <>
                Model said <span className="font-medium">“{short(miss.s.output) || "(nothing)"}”</span>; expected{" "}
                <span className="font-medium">{plainRules(short(Array.isArray(miss.s.expected) ? miss.s.expected[0] : miss.s.expected, 60))}</span>
              </>
            ) : (
              "No mistakes in this run."
            )}
          </Fact>
        </div>
      )}
    </div>
  );
}

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5 text-sm">
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="break-words">{children}</p>
    </div>
  );
}
