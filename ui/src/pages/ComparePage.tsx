import { AlertTriangle } from "lucide-react";
import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type RunSummary } from "../api";
import { Card, CardTitle, ErrorBox, InfoBox, Loading, PageTitle, UnreviewedBanner } from "../components";
import { MAX_COMPARE, SERIES, pct, taskLabel, useLoad, when } from "../lib";

function warnings(runs: RunSummary[]): string[] {
  const out: string[] = [];
  const s0 = JSON.stringify(runs[0].settings);
  if (runs.some((r) => JSON.stringify(r.settings) !== s0)) out.push("These tests used different settings, so the comparison is not fully fair.");
  const tasks0 = runs[0].tasks.map((t) => `${t.task}:${t.n}`).join(",");
  if (runs.some((r) => r.tasks.map((t) => `${t.task}:${t.n}`).join(",") !== tasks0))
    out.push("These tests used different topics or numbers of questions. Compare only the topics both have, and remember small numbers are rough.");
  const days = new Set(runs.map((r) => r.started_at.slice(0, 10)));
  if (days.size > 1) out.push("These tests were run on different days. Online models can change over time.");
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
    <div className="space-y-12">
      <PageTitle
        title="Compare tests"
        sub={`Put up to ${MAX_COMPARE} tests side by side, topic by topic. Each test gets its own colour, and every bar shows its number.`}
      />

      <Card>
        <CardTitle hint={`Tick 2 or ${MAX_COMPARE} tests (${ids.length} ticked).`}>Choose tests</CardTitle>
        {all.length === 0 && <p className="text-sm text-muted">No tests yet. <Link className="text-link underline" to="/new">Start one</Link>.</p>}
        <div className="grid gap-3 sm:grid-cols-2">
          {all.map((r) => {
            const idx = ids.indexOf(r.run_id);
            return (
              <label key={r.run_id} className={`flex items-center gap-3 rounded-xl border p-4 text-sm transition-colors duration-150 ${idx >= 0 ? "border-accent bg-info-bg" : "border-line hover:bg-surface-2"}`}>
                <input type="checkbox" className="accent-[var(--accent)]" checked={idx >= 0} disabled={idx < 0 && ids.length >= MAX_COMPARE} onChange={() => toggle(r.run_id)} />
                {idx >= 0 && <span aria-hidden className="inline-block size-3 shrink-0 rounded-sm" style={{ background: SERIES[idx] }} />}
                <span className="min-w-0">
                  <span className="block break-all font-mono text-[12px] font-medium">{r.model}</span>
                  <span className="block text-xs text-muted">{when(r.started_at)} · {r.total_n} questions</span>
                </span>
              </label>
            );
          })}
        </div>
      </Card>

      {runs.length < 2 && (
        <InfoBox>Tick at least two tests above to see them side by side.</InfoBox>
      )}

      {runs.length >= 2 && (
        <>
          {runs.some((r) => r.allow_unreviewed) && <UnreviewedBanner />}
          {warnings(runs).map((w) => (
            <p key={w} className="flex items-start gap-3 rounded-xl bg-warn-bg p-4 text-sm text-warn">
              <AlertTriangle aria-hidden className="mt-0.5 size-4 shrink-0" /> {w}
            </p>
          ))}

          <Card>
            <CardTitle hint="Longer bar = more questions correct in that topic. The colour shows which test it is.">Scores by topic</CardTitle>
            <ul className="mb-6 flex flex-wrap gap-6 text-sm" aria-label="Legend">
              {runs.map((r, i) => (
                <li key={r.run_id} className="flex items-center gap-2">
                  <span aria-hidden className="inline-block size-3 rounded-sm" style={{ background: SERIES[i] }} />
                  <span className="font-mono text-[12px]">{r.model}</span>
                </li>
              ))}
            </ul>
            <div className="space-y-6">
              {taskNames.map((task) => (
                <figure key={task}>
                  <figcaption className="mb-2 text-sm font-medium">{taskLabel(task)}</figcaption>
                  <div className="space-y-1.5">
                    {runs.map((r, i) => {
                      const t = score(r, task);
                      return (
                        <div key={r.run_id} className="flex items-center gap-3" title={`${r.model} · ${taskLabel(task)}: ${t ? pct(t.score) : "not tested"}`}>
                          <div className="h-3 flex-1 overflow-hidden rounded-full bg-surface-2" aria-hidden>
                            <div className="h-full rounded-full transition-[width] duration-300" style={{ width: `${(t?.score ?? 0) * 100}%`, background: SERIES[i] }} />
                          </div>
                          <span className="tabular w-28 text-right text-xs">{t ? `${pct(t.score)} · n=${t.n}` : "not tested"}</span>
                        </div>
                      );
                    })}
                  </div>
                </figure>
              ))}
            </div>
          </Card>

          <Card className="p-0">
            <div className="p-6 pb-4">
              <h2 className="text-base font-semibold text-primary">Same numbers as a table</h2>
            </div>
            <div className="overflow-x-auto border-t border-line">
              <table className="w-full min-w-[560px] text-sm">
                <thead className="bg-surface-2 text-left text-xs uppercase tracking-wide text-muted">
                  <tr>
                    <th className="px-6 py-3 font-semibold">Topic</th>
                    {runs.map((r) => <th key={r.run_id} className="px-6 py-3 text-right font-mono text-[11px] font-semibold normal-case">{r.model}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {taskNames.map((task) => (
                    <tr key={task} className="border-t border-line">
                      <td className="px-6 py-3 font-medium">{taskLabel(task)}</td>
                      {runs.map((r) => {
                        const t = score(r, task);
                        return <td key={r.run_id} className="tabular px-6 py-3 text-right">{t ? `${pct(t.score)} (n=${t.n})` : "-"}</td>;
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <p className="text-xs text-muted">This page does not pick a winner. With only a few questions, close scores can easily swap on another day.</p>
        </>
      )}
    </div>
  );
}
