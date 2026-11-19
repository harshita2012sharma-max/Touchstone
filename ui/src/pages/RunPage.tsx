import { ExternalLink } from "lucide-react";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api, type Sample } from "../api";
import { Card, CardTitle, ErrorBox, InfoBox, Loading, Meta, PageTitle, UnreviewedBanner, buttonSecondary, inputClass } from "../components";
import { pct, plainRules, taskLabel, useLoad, when } from "../lib";
import { StoneHero } from "../StoneHero";

const LIMITATIONS = [
  "Few questions per topic, so a difference of a few percent is often just luck.",
  "Hindi does not represent all of India; other languages are not tested.",
  "Hinglish has no fixed spelling, so a correct answer can sometimes be marked wrong.",
  "Translation is scored by word overlap, which can be strict on good paraphrases.",
  "Online models can change without a new name; check the date and the model id.",
];

function expectedText(s: Sample) {
  return Array.isArray(s.expected) ? s.expected.join(" / ") : s.expected;
}

export function RunPage() {
  const { runId = "" } = useParams();
  const { data: run, error } = useLoad(() => api.run(runId), [runId]);
  const [task, setTask] = useState("all");
  const [onlyWrong, setOnlyWrong] = useState(false);
  const [query, setQuery] = useState("");

  const rows = useMemo(() => {
    if (!run) return [];
    const q = query.toLowerCase();
    return run.tasks
      .filter((t) => task === "all" || t.task === task)
      .flatMap((t) => t.samples.map((s) => ({ task: t.task, s })))
      .filter(({ s }) => !onlyWrong || s.score < 1)
      .filter(({ s }) => !q || `${s.sample_id} ${s.prompt} ${s.output}`.toLowerCase().includes(q));
  }, [run, task, onlyWrong, query]);

  if (error) return <ErrorBox message={error} />;
  if (!run) return <Loading />;
  const { metadata: m, config: c } = run;
  const unparsed = run.tasks.filter((t) => t.unparsed_rate > 0);

  return (
    <div className="space-y-8">
      <PageTitle
        title={`Result: ${c.model}`}
        sub={`Tested on ${when(m.started_at)}. Below: the overall score, a score for each topic, and every question with the model's answer.`}
        action={
          <a href={api.reportUrl(m.run_id)} target="_blank" rel="noreferrer" className={buttonSecondary}>
            <ExternalLink aria-hidden className="size-4" /> Open shareable report
          </a>
        }
      />
      {c.allow_unreviewed && <UnreviewedBanner />}

      <StoneHero run={run} />

      <InfoBox title="How to read this">
        The score is the share of questions answered correctly. “n” is how many questions were asked; with a small n the
        score is only a rough trial.
        {unparsed.length > 0 && (
          <> Some answers were unclear and counted as wrong (“unparsed”): {unparsed.map((t) => `${taskLabel(t.task)} ${pct(t.unparsed_rate, 0)}`).join(", ")}.</>
        )}
      </InfoBox>

      <section aria-label="Test details" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Meta label="Model you chose"><span className="font-mono text-[13px]">{c.model}</span></Meta>
        <Meta label="Model the provider used"><span className="font-mono text-[13px]">{m.provider_model_id ?? "not reported"}</span></Meta>
        <Meta label="Settings (same for all)">temperature {c.settings.temperature} · seed {c.settings.seed}</Meta>
        <Meta label="Questions asked">{run.tasks.reduce((a, t) => a + t.n, 0)}{c.limit ? ` (up to ${c.limit} per topic)` : ""}</Meta>
      </section>

      <Card className="p-0">
        <div className="p-6 pb-4">
          <h2 className="text-base font-semibold text-primary">Every question and answer</h2>
          <p className="mt-1 text-sm text-muted">
            Check any answer yourself. “Expected” is the correct answer, “Read as” is what touchstone understood from the model's reply.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <label className="sr-only" htmlFor="task-filter">Topic</label>
            <select id="task-filter" className={`${inputClass} w-auto`} value={task} onChange={(e) => setTask(e.target.value)}>
              <option value="all">All topics</option>
              {run.tasks.map((t) => <option key={t.task} value={t.task}>{taskLabel(t.task)}</option>)}
            </select>
            <label className="sr-only" htmlFor="search">Search</label>
            <input id="search" className={`${inputClass} w-56`} placeholder="Search questions and answers" value={query} onChange={(e) => setQuery(e.target.value)} />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="accent-[var(--accent)]" checked={onlyWrong} onChange={(e) => setOnlyWrong(e.target.checked)} /> Only mistakes
            </label>
            <span className="text-sm text-muted">{rows.length} shown</span>
          </div>
        </div>
        <div className="overflow-x-auto border-t border-line">
          <table className="w-full min-w-[760px] table-fixed text-sm">
            <thead className="bg-surface-2 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="w-44 px-6 py-3 font-semibold">Topic</th>
                <th className="px-3 py-3 font-semibold">Model's answer</th>
                <th className="w-36 px-3 py-3 font-semibold">Expected</th>
                <th className="w-28 px-3 py-3 font-semibold">Read as</th>
                <th className="w-24 px-6 py-3 text-right font-semibold">Result</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ task: tn, s }) => (
                <tr key={`${tn}-${s.sample_id}`} className="border-t border-line align-top">
                  <td className="px-6 py-4">
                    <div className="font-medium">{taskLabel(tn)}</div>
                    <div className="font-mono text-[11px] text-muted break-all">{s.sample_id}</div>
                  </td>
                  <td className="px-3 py-4">
                    <details>
                      <summary className="text-xs font-medium text-link">Show the question</summary>
                      <pre className="mt-2 whitespace-pre-wrap break-words rounded-lg bg-surface-2 p-3 font-mono text-[12px]">{s.prompt}</pre>
                    </details>
                    <pre className="mt-2 whitespace-pre-wrap break-words font-sans">{s.output || <span className="text-muted">(no answer)</span>}</pre>
                  </td>
                  <td className="px-3 py-4 break-words">{plainRules(expectedText(s))}</td>
                  <td className="px-3 py-4 break-words">{s.parsed ? plainRules(s.parsed) : s.unparsed ? <span className="text-warn">unclear</span> : "-"}</td>
                  <td className="px-6 py-4 text-right">
                    <span className={`inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${s.score >= 1 ? "bg-info-bg text-info" : "bg-warn-bg text-warn"}`}>
                      {s.score >= 1 ? "Correct" : s.score > 0 ? pct(s.score, 0) : "Wrong"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card>
        <CardTitle hint="Please keep these in mind before sharing any number.">Limits of this test</CardTitle>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          {LIMITATIONS.map((l) => <li key={l}>{l}</li>)}
        </ul>
      </Card>
    </div>
  );
}
