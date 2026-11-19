import { GitCompare, Play } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import {
  Card,
  CardTitle,
  ErrorBox,
  Glossary,
  Loading,
  PageTitle,
  StepCard,
  UnreviewedBadge,
  buttonPrimary,
  buttonSecondary,
} from "../components";
import { MAX_COMPARE, pct, useLoad, when } from "../lib";

export function RunsPage() {
  const { data: runs, error } = useLoad(api.runs);
  const [picked, setPicked] = useState<string[]>([]);
  const navigate = useNavigate();

  const toggle = (id: string) =>
    setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : p.length < MAX_COMPARE ? [...p, id] : p));

  return (
    <div className="space-y-8">
      <PageTitle
        title="Test AI models in Hindi and Hinglish"
        sub="touchstone gives an AI model a short exam, checks every answer with fixed rules, and shows how it did. Everything stays on this computer."
        action={
          <Link to="/new" className={buttonPrimary}>
            <Play aria-hidden className="size-4" /> Start a new test
          </Link>
        }
      />

      <section aria-label="How it works" className="grid gap-6 md:grid-cols-3">
        <StepCard n={1} title="Pick a model and topics">
          Choose an AI model (for example Gemini or Llama) and which kinds of questions to ask.
        </StepCard>
        <StepCard n={2} title="It answers the questions">
          Each question is sent to the model, and every answer is checked automatically.
        </StepCard>
        <StepCard n={3} title="See the result">
          You get a score for each topic and can open every question and answer to check.
        </StepCard>
      </section>

      <Card className="p-0">
        <div className="flex flex-wrap items-center justify-between gap-4 p-6 pb-4">
          <div>
            <h2 className="text-base font-semibold text-primary">Your past tests</h2>
            <p className="mt-1 text-sm text-muted">
              Click a model name to see its full result. Tick 2 or 3 boxes to compare them.
            </p>
          </div>
          <button
            type="button"
            className={buttonSecondary}
            disabled={picked.length < 2}
            onClick={() => navigate(`/compare?runs=${picked.map(encodeURIComponent).join(",")}`)}
          >
            <GitCompare aria-hidden className="size-4" /> Compare ticked ({picked.length}/{MAX_COMPARE})
          </button>
        </div>
        {error && <div className="px-6 pb-6"><ErrorBox message={error} /></div>}
        {!runs && !error && <div className="px-6 pb-6"><Loading /></div>}
        {runs && runs.length === 0 && (
          <div className="px-6 pb-8 text-sm text-muted">
            No tests yet. Press <span className="font-semibold text-text">Start a new test</span> to run your first one.
          </div>
        )}
        {runs && runs.length > 0 && (
          <div className="overflow-x-auto border-t border-line">
            <table className="w-full min-w-[680px] text-sm">
              <thead className="bg-surface-2 text-left text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="w-14 px-6 py-3 font-semibold"><span className="sr-only">Tick to compare</span></th>
                  <th className="px-3 py-3 font-semibold">Model</th>
                  <th className="px-3 py-3 font-semibold">When</th>
                  <th className="px-3 py-3 text-right font-semibold">Questions</th>
                  <th className="px-6 py-3 text-right font-semibold">Overall score</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.run_id} className="border-t border-line hover:bg-surface-2">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        className="size-4 accent-[var(--accent)]"
                        aria-label={`Tick ${r.model} to compare`}
                        checked={picked.includes(r.run_id)}
                        disabled={!picked.includes(r.run_id) && picked.length >= MAX_COMPARE}
                        onChange={() => toggle(r.run_id)}
                      />
                    </td>
                    <td className="px-3 py-4">
                      <Link to={`/runs/${encodeURIComponent(r.run_id)}`} className="font-mono text-[13px] font-medium text-link hover:underline">
                        {r.model}
                      </Link>
                      {r.allow_unreviewed && <UnreviewedBadge />}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-muted">{when(r.started_at)}</td>
                    <td className="tabular px-3 py-4 text-right">{r.total_n}</td>
                    <td className="tabular px-6 py-4 text-right font-semibold">{pct(r.mean_score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card>
        <CardTitle hint="What the words and numbers on these pages mean.">Words you will see</CardTitle>
        <Glossary />
      </Card>
    </div>
  );
}
