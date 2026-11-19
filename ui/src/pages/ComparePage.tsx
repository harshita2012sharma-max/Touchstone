import { AlertTriangle } from "lucide-react";
import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type RunSummary } from "../api";
import { Card, ErrorBox, Loading, PageTitle, UnreviewedBanner } from "../components";
import { MAX_COMPARE, SERIES, pct, useLoad, when } from "../lib";

function warnings(runs: RunSummary[]): string[] {
  const out: string[] = [];
  const s0 = JSON.stringify(runs[0].settings);
  if (runs.some((r) => JSON.stringify(r.settings) !== s0)) out.push("Settings differ between runs.");
  const tasks0 = runs[0].tasks.map((t) => `${t.task}:${t.n}`).join(",");
  if (runs.some((r) => r.tasks.map((t) => `${t.task}:${t.n}`).join(",") !== tasks0))
    out.push("Runs used different tasks or numbers of items; only shared tasks are directly comparable.");
  const days = new Set(runs.map((r) => r.started_at.slice(0, 10)));
  if (days.size > 1) out.push("Runs were made on different dates; API models can change over time.");
  return out;
}

export function ComparePage() {
  const [params, setParams] = useSearchParams();
  const { data: all, error } = useLoad(api.runs);
  const ids = (params.get("runs") ?? "").split(",").filter(Boolean).slice(0, MAX_COMPARE);

  const runs = useMemo(
    () => (all ? ids.map((id) => all.find((r) => r.run_id === id)).filter((r): r is RunSummary => !!r) : []),
    [all, ids.join(",")], // eslint-disable-line react-hooks/exhaustive-deps
  );
  const taskNames = useMemo(() => [...new Set(runs.flatMap((r) => r.tasks.map((t) => t.task)))], [runs]);

  const toggle = (id: string) => {
    const next = ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id].slice(0, MAX_COMPARE);
    setParams(next.length ? { runs: next.join(",") } : {});
  };

  if (error) return <ErrorBox message={error} />;
  if (!all) return <Loading />;

  const score = (r: RunSummary, task: string) => r.tasks.find((t) => t.task === task);

  return (
    <>
      <PageTitle title="Compare" sub={`Pick 2 or ${MAX_COMPARE} runs. Same settings and items make the comparison fair.`} />
      <Card className="mb-4">
        <h2 className="mb-2 text-sm font-medium">Runs ({ids.length}/{MAX_COMPARE})</h2>
        {all.length === 0 && <p className="text-sm text-muted">No runs yet. <Link className="underline" to="/new">Start one</Link>.</p>}
        <div className="flex flex-wrap gap-2">
          {all.map((r) => {
            const idx = ids.indexOf(r.run_id);
            return (
              <label key={r.run_id} className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm ${idx >= 0 ? "border-primary" : "border-line"}`}>
                <input
                  type="checkbox"
                  checked={idx >= 0}
                  disabled={idx < 0 && ids.length >= MAX_COMPARE}
                  onChange={() => toggle(r.run_id)}
                />
                {idx >= 0 && <span aria-hidden className="inline-block size-3 rounded-sm" style={{ background: SERIES[idx] }} />}
                <span className="font-mono text-[12px]">{r.model}</span>
                <span className="text-xs text-muted">{when(r.started_at)}</span>
              </label>
            );
          })}
        </div>
      </Card>

      {runs.length >= 2 && (
        <>
          {runs.some((r) => r.allow_unreviewed) && <UnreviewedBanner />}
          {warnings(runs).map((w) => (
            <p key={w} className="mb-2 flex items-start gap-2 rounded-lg bg-warn-bg px-3 py-2 text-sm text-warn">
              <AlertTriangle aria-hidden className="mt-0.5 size-4 shrink-0" /> {w}
            </p>
          ))}

          <Card className="mb-4">
            <ul className="mb-4 flex flex-wrap gap-4 text-sm" aria-label="Legend">
              {runs.map((r, i) => (
                <li key={r.run_id} className="flex items-center gap-2">
                  <span aria-hidden className="inline-block size-3 rounded-sm" style={{ background: SERIES[i] }} />
                  <span className="font-mono text-[12px]">{r.model}</span>
                </li>
              ))}
            </ul>
            <div className="space-y-5">
              {taskNames.map((task) => (
                <figure key={task}>
                  <figcaption className="mb-1 font-mono text-[13px]">{task}</figcaption>
                  <div className="space-y-[2px]">
                    {runs.map((r, i) => {
                      const t = score(r, task);
                      return (
                        <div key={r.run_id} className="flex items-center gap-2" title={`${r.model} · ${task}: ${t ? pct(t.score) : "not run"}${t ? ` (n=${t.n})` : ""}`}>
                          <div className="h-3 flex-1 rounded-r-sm" aria-hidden>
                            <div className="streak h-full rounded-r-[4px]" style={{ width: `${(t?.score ?? 0) * 100}%`, background: SERIES[i], animationDelay: `${i * 120}ms` }} />
                          </div>
                          <span className="tabular w-24 text-right text-xs">
                            {t ? `${pct(t.score)} · n=${t.n}` : "not run"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </figure>
              ))}
            </div>
          </Card>

          <Card className="overflow-x-auto p-0">
            <table className="w-full min-w-[560px] text-sm">
              <caption className="sr-only">Scores per task for each run</caption>
              <thead className="text-left text-muted">
                <tr className="border-b border-line">
                  <th className="px-3 py-2 font-medium">Task</th>
                  {runs.map((r) => <th key={r.run_id} className="px-3 py-2 text-right font-mono text-[12px] font-medium">{r.model}</th>)}
                </tr>
              </thead>
              <tbody>
                {taskNames.map((task) => (
                  <tr key={task} className="border-b border-line last:border-0">
                    <td className="px-3 py-2 font-mono text-[13px]">{task}</td>
                    {runs.map((r) => {
                      const t = score(r, task);
                      return <td key={r.run_id} className="tabular px-3 py-2 text-right">{t ? `${pct(t.score)} (n=${t.n})` : "-"}</td>;
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          <p className="mt-3 text-xs text-muted">No ranking is implied. With small n, overlapping results are common.</p>
        </>
      )}
    </>
  );
}
