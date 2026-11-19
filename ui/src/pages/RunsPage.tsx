import { GitCompare, Play } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { Card, ErrorBox, Loading, PageTitle, UnreviewedBadge, buttonPrimary, buttonSecondary } from "../components";
import { MAX_COMPARE, pct, useLoad, when } from "../lib";

export function RunsPage() {
  const { data: runs, error } = useLoad(api.runs);
  const [picked, setPicked] = useState<string[]>([]);
  const navigate = useNavigate();

  const toggle = (id: string) =>
    setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : p.length < MAX_COMPARE ? [...p, id] : p));

  return (
    <>
      <PageTitle
        title="Runs"
        sub="Saved results on this computer. Each score is the share of items answered correctly."
        action={
          <button
            type="button"
            className={buttonSecondary}
            disabled={picked.length < 2}
            onClick={() => navigate(`/compare?runs=${picked.map(encodeURIComponent).join(",")}`)}
          >
            <GitCompare aria-hidden className="size-4" /> Compare selected ({picked.length}/{MAX_COMPARE})
          </button>
        }
      />
      {error && <ErrorBox message={error} />}
      {!runs && !error && <Loading />}
      {runs && runs.length === 0 && (
        <Card className="text-center">
          <h2 className="text-lg font-medium">Start your first run</h2>
          <p className="mt-1 text-sm text-muted">Pick a model and tasks. Results are saved in the runs folder.</p>
          <Link to="/new" className={`${buttonPrimary} mt-4`}>
            <Play aria-hidden className="size-4" /> New run
          </Link>
        </Card>
      )}
      {runs && runs.length > 0 && (
        <Card className="overflow-x-auto p-0">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="text-left text-muted">
              <tr className="border-b border-line">
                <th className="w-10 px-3 py-2 font-medium"><span className="sr-only">Select to compare</span></th>
                <th className="px-3 py-2 font-medium">Model</th>
                <th className="px-3 py-2 font-medium">Date</th>
                <th className="px-3 py-2 text-right font-medium">Tasks</th>
                <th className="px-3 py-2 text-right font-medium">n</th>
                <th className="px-3 py-2 text-right font-medium">Mean score</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.run_id} className="border-b border-line last:border-0 hover:bg-surface-2">
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      aria-label={`Select ${r.model} for comparison`}
                      checked={picked.includes(r.run_id)}
                      disabled={!picked.includes(r.run_id) && picked.length >= MAX_COMPARE}
                      onChange={() => toggle(r.run_id)}
                    />
                  </td>
                  <td className="px-3 py-2">
                    <Link to={`/runs/${encodeURIComponent(r.run_id)}`} className="font-mono text-[13px] hover:underline">
                      {r.model}
                    </Link>
                    {r.allow_unreviewed && <UnreviewedBadge />}
                    {r.provider_model_id && (
                      <div className="text-xs text-muted">ran as {r.provider_model_id}</div>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2">{when(r.started_at)}</td>
                  <td className="tabular px-3 py-2 text-right">{r.tasks.length}</td>
                  <td className="tabular px-3 py-2 text-right">{r.total_n}</td>
                  <td className="tabular px-3 py-2 text-right">{pct(r.mean_score)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      <p className="mt-3 text-xs text-muted">
        Mean score averages the task scores. Small samples: treat differences of a few points as noise.
      </p>
    </>
  );
}
