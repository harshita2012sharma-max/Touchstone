import { ExternalLink } from "lucide-react";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api, type Sample } from "../api";
import { Card, ErrorBox, Loading, Meta, PageTitle, UnreviewedBanner, buttonSecondary, inputClass } from "../components";
import { StoneHero } from "../StoneHero";
import { pct, useLoad, when } from "../lib";

const LIMITATIONS = [
  "Small dataset: a few points of difference is often noise.",
  "Hindi does not represent all of India.",
  "Hinglish spelling varies, so rule-based scoring can miss valid answers.",
  "Translation uses chrF, a rough signal that can penalise good paraphrases.",
  "API models can change behind the same name; check the reported model id and date.",
];

function expectedText(s: Sample) {
  return Array.isArray(s.expected) ? s.expected.join(" / ") : s.expected;
}

export function RunPage() {
  const { runId = "" } = useParams();
  const { data: run, error } = useLoad(() => api.run(runId), [runId]);
  const [task, setTask] = useState("all");
  const [onlyWrong, setOnlyWrong] = useState(false);
  const [onlyUnparsed, setOnlyUnparsed] = useState(false);
  const [query, setQuery] = useState("");

  const rows = useMemo(() => {
    if (!run) return [];
    const q = query.toLowerCase();
    return run.tasks
      .filter((t) => task === "all" || t.task === task)
      .flatMap((t) => t.samples.map((s) => ({ task: t.task, s })))
      .filter(({ s }) => (!onlyWrong || s.score < 1) && (!onlyUnparsed || s.unparsed))
      .filter(({ s }) => !q || `${s.sample_id} ${s.prompt} ${s.output}`.toLowerCase().includes(q));
  }, [run, task, onlyWrong, onlyUnparsed, query]);

  if (error) return <ErrorBox message={error} />;
  if (!run) return <Loading />;
  const { metadata: m, config: c } = run;
  const totalN = run.tasks.reduce((a, t) => a + t.n, 0);

  return (
    <>
      <PageTitle
        title={c.model}
        sub={when(m.started_at)}
        action={
          <a href={api.reportUrl(m.run_id)} target="_blank" rel="noreferrer" className={buttonSecondary}>
            <ExternalLink aria-hidden className="size-4" /> HTML report
          </a>
        }
      />
      {c.allow_unreviewed && <UnreviewedBanner />}
      <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <Meta label="Model id reported"><span className="font-mono text-[13px]">{m.provider_model_id ?? "not reported"}</span></Meta>
        <Meta label="Settings">temperature {c.settings.temperature} · seed {c.settings.seed} · top_p {c.settings.top_p} · max tokens {c.settings.max_tokens}</Meta>
        <Meta label="Samples">{totalN} across {run.tasks.length} task(s){c.limit ? ` (limit ${c.limit} each)` : ""}</Meta>
        <Meta label="touchstone">{m.tool_version}{m.git_sha ? ` (${m.git_sha})` : ""}</Meta>
      </div>

      <StoneHero run={run} />
      {run.tasks.some((t) => t.unparsed_rate > 0) && (
        <p className="mb-4 text-sm text-muted">
          Unparsed answers (no clear answer found, counted as wrong):{" "}
          {run.tasks.filter((t) => t.unparsed_rate > 0).map((t) => `${t.task} ${pct(t.unparsed_rate, 0)}`).join(", ")}.
        </p>
      )}
      <Card>
        <h2 className="mb-2 font-medium">Limitations</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          {LIMITATIONS.map((l) => <li key={l}>{l}</li>)}
        </ul>
      </Card>

      <h2 className="mb-3 mt-8 text-lg font-medium">Items</h2>
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <label className="sr-only" htmlFor="task-filter">Task</label>
        <select id="task-filter" className={`${inputClass} w-auto`} value={task} onChange={(e) => setTask(e.target.value)}>
          <option value="all">All tasks</option>
          {run.tasks.map((t) => <option key={t.task} value={t.task}>{t.task}</option>)}
        </select>
        <label className="sr-only" htmlFor="search">Search prompts and outputs</label>
        <input id="search" className={`${inputClass} w-56`} placeholder="Search text" value={query} onChange={(e) => setQuery(e.target.value)} />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={onlyWrong} onChange={(e) => setOnlyWrong(e.target.checked)} /> Not full marks
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={onlyUnparsed} onChange={(e) => setOnlyUnparsed(e.target.checked)} /> Unparsed only
        </label>
        <span className="text-sm text-muted">{rows.length} shown</span>
      </div>
      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[720px] table-fixed text-sm">
          <thead className="text-left text-muted">
            <tr className="border-b border-line">
              <th className="w-48 px-3 py-2 font-medium">Item</th>
              <th className="px-3 py-2 font-medium">Model output</th>
              <th className="w-36 px-3 py-2 font-medium">Expected</th>
              <th className="w-28 px-3 py-2 font-medium">Parsed</th>
              <th className="w-16 px-3 py-2 text-right font-medium">Score</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ task: tn, s }) => (
              <tr key={`${tn}-${s.sample_id}`} className="border-b border-line align-top last:border-0">
                <td className="px-3 py-2 font-mono text-[12px] break-all">{s.sample_id}</td>
                <td className="px-3 py-2">
                  <details>
                    <summary className="text-xs text-muted">Show prompt</summary>
                    <pre className="mt-1 rounded bg-surface-2 p-2 font-mono text-[12px] whitespace-pre-wrap break-words">{s.prompt}</pre>
                  </details>
                  <pre className="mt-1 font-sans whitespace-pre-wrap break-words">{s.output || <span className="text-muted">(empty reply)</span>}</pre>
                </td>
                <td className="px-3 py-2 break-words">{expectedText(s)}</td>
                <td className="px-3 py-2 break-words">{s.parsed ?? (s.unparsed ? <span className="text-warn">unparsed</span> : "-")}</td>
                <td className="tabular px-3 py-2 text-right">{s.score.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
