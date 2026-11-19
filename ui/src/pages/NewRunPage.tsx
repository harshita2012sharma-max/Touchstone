import { KeyRound, Play, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Provider } from "../api";
import { Card, CardTitle, ErrorBox, Hint, InfoBox, Loading, PageTitle, buttonPrimary, buttonSecondary, inputClass } from "../components";
import { taskLabel, useLoad } from "../lib";

const KEY_VARS: Record<string, string> = {
  groq: "GROQ_API_KEY",
  gemini: "GEMINI_API_KEY",
  openrouter: "OPENROUTER_API_KEY",
};

const PROVIDER_NOTES: Record<string, string> = {
  gemini: "Google's models. Free key from Google AI Studio.",
  groq: "Very fast. Runs open models like Llama, Qwen and GPT-OSS.",
  openrouter: "Many models in one place. Free ones end in \":free\" and are often busy.",
  ollama: "Runs a small model on this computer. No key, works offline.",
  mock: "A pretend model for practice. Always answers \"A\". No key needed.",
};

function usable(p: Provider) {
  return !p.needs_key || p.key_set;
}

export function NewRunPage() {
  const { data: status, error } = useLoad(api.status);
  const navigate = useNavigate();
  const [provider, setProvider] = useState("");
  const [models, setModels] = useState<string[] | null>(null);
  const [modelsAsOf, setModelsAsOf] = useState("");
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [model, setModel] = useState("");
  const [tasks, setTasks] = useState<string[]>([]);
  const [drafts, setDrafts] = useState(false);
  const [limit, setLimit] = useState("2");
  const [maxTokens, setMaxTokens] = useState("512");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!status) return;
    const first = status.providers.find((p) => p.name !== "mock" && usable(p)) ?? status.providers.find(usable);
    if (first && !provider) setProvider(first.name);
    if (status.drafts_available && status.tasks.every((t) => t.items === 0)) setDrafts(true);
  }, [status, provider]);

  const current = status?.providers.find((p) => p.name === provider);

  const loadModels = () => {
    if (!current || !usable(current)) return;
    setModels(null);
    setModelsError(null);
    setModel("");
    api
      .models(provider)
      .then((r) => {
        setModels(r.models);
        setModelsAsOf(r.as_of);
      })
      .catch((e: Error) => setModelsError(e.message));
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(loadModels, [provider, current?.key_set]);

  const shown = useMemo(
    () => (models ?? []).filter((m) => m.toLowerCase().includes(filter.toLowerCase())),
    [models, filter],
  );

  if (error) return <ErrorBox message={error} />;
  if (!status) return <Loading />;

  const count = (name: string) => {
    const t = status.tasks.find((x) => x.name === name);
    return t ? (drafts ? t.draft_items : t.items) : 0;
  };
  const toggleTask = (name: string) =>
    setTasks((ts) => (ts.includes(name) ? ts.filter((t) => t !== name) : [...ts, name]));
  const allTasks = status.tasks.map((t) => t.name);
  const limitNum = limit.trim() === "" ? null : Number(limit);
  const tokensNum = Number(maxTokens);
  const questions = tasks.reduce((a, t) => a + Math.min(count(t), limitNum ?? Infinity), 0);
  const problems: string[] = [];
  if (!model) problems.push("Choose a model in step 2.");
  if (tasks.length === 0) problems.push("Tick at least one topic in step 3.");
  if (tasks.some((t) => count(t) === 0)) problems.push("Some ticked topics have no questions yet. Turn on draft questions or untick them.");
  if (limitNum !== null && (!Number.isInteger(limitNum) || limitNum < 1)) problems.push("Questions per topic must be a whole number, 1 or more.");
  if (!Number.isInteger(tokensNum) || tokensNum < 1 || tokensNum > 8192) problems.push("Max answer length must be between 1 and 8192.");

  const start = async () => {
    setSubmitError(null);
    if (problems.length) {
      setSubmitError(problems.join(" "));
      return;
    }
    setSubmitting(true);
    try {
      const { job_id } = await api.startJob({ model: `${provider}/${model}`, tasks, limit: limitNum, max_tokens: tokensNum, drafts });
      navigate(`/jobs/${job_id}`);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : String(e));
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <PageTitle
        title="Start a new test"
        sub="Follow the three steps. Every model gets exactly the same questions and settings, so results can be compared fairly."
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          <Card>
            <CardTitle hint="Where the AI model runs. Pick one that says “ready”.">1. Choose a provider</CardTitle>
            <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Provider">
              {status.providers.map((p) => {
                const ready = usable(p);
                return (
                  <label
                    key={p.name}
                    className={`flex gap-3 rounded-xl border p-4 transition-colors duration-150 ${
                      provider === p.name ? "border-accent bg-info-bg" : "border-line hover:bg-surface-2"
                    }`}
                  >
                    <input
                      type="radio"
                      name="provider"
                      className="mt-1 accent-[var(--accent)]"
                      aria-label={`${p.name}, ${ready ? "ready" : "needs a key"}`}
                      checked={provider === p.name}
                      onChange={() => setProvider(p.name)}
                    />
                    <span className="min-w-0">
                      <span className="flex items-center gap-2">
                        <span className="font-semibold capitalize">{p.name === "mock" ? "Practice (mock)" : p.name}</span>
                        <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${ready ? "bg-info-bg text-info" : "bg-warn-bg text-warn"}`}>
                          {ready ? "ready" : "needs a key"}
                        </span>
                      </span>
                      <span className="mt-1 block text-xs text-muted">{PROVIDER_NOTES[p.name] ?? ""}</span>
                    </span>
                  </label>
                );
              })}
            </div>
            {current && !usable(current) && (
              <div className="mt-4">
                <InfoBox title="This provider needs an API key">
                  Add the line <code className="font-mono">{KEY_VARS[current.name] ?? "API_KEY"}=your-key</code> to the{" "}
                  <code className="font-mono">.env</code> file in the folder where you started touchstone, then restart{" "}
                  <code className="font-mono">touchstone ui</code>. The key stays on your computer.
                  <KeyRound aria-hidden className="ml-1 inline size-4" />
                </InfoBox>
              </div>
            )}
          </Card>

          {current && usable(current) && (
            <Card>
              <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h2 className="text-base font-semibold text-primary">2. Choose a model</h2>
                  <p className="mt-1 text-sm text-muted">
                    This list comes live from {current.name}{modelsAsOf ? ` (${modelsAsOf})` : ""}. Type part of a name to filter, then click one.
                  </p>
                </div>
                <button type="button" className={buttonSecondary} onClick={loadModels}>
                  <RefreshCw aria-hidden className="size-4" /> Refresh
                </button>
              </div>
              {modelsError && <ErrorBox message={modelsError} />}
              {!models && !modelsError && <Loading label="Getting the model list" />}
              {models && models.length === 0 && (
                <InfoBox title="No models found">
                  {provider === "ollama" ? (
                    <>Ollama is running but has no models yet. Download a small one first, e.g. run <code className="font-mono">ollama pull qwen2.5:1.5b</code> in a terminal, then press Refresh.</>
                  ) : (
                    <>This provider returned an empty list. Press Refresh, or pick another provider.</>
                  )}
                </InfoBox>
              )}
              {models && models.length > 0 && (
                <>
                  <label className="sr-only" htmlFor="model-filter">Filter models</label>
                  <input id="model-filter" className={`${inputClass} w-full`} placeholder="Type to filter, e.g. flash or llama" value={filter} onChange={(e) => setFilter(e.target.value)} />
                  <label className="sr-only" htmlFor="model-select">Model</label>
                  <select id="model-select" size={7} className={`${inputClass} mt-3 h-auto w-full py-2 font-mono`} value={model} onChange={(e) => setModel(e.target.value)}>
                    <option value="" disabled>Choose a model</option>
                    {shown.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <Hint>{model ? <>Chosen: <span className="font-mono font-medium text-text">{model}</span></> : "No model chosen yet."}</Hint>
                </>
              )}
            </Card>
          )}

          <Card>
            <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold text-primary">3. Choose topics</h2>
                <p className="mt-1 text-sm text-muted">Each topic is a small set of questions of one kind.</p>
              </div>
              <button type="button" className={buttonSecondary} onClick={() => setTasks(tasks.length === allTasks.length ? [] : allTasks)}>
                {tasks.length === allTasks.length ? "Untick all" : "Tick all"}
              </button>
            </div>
            {status.drafts_available && (
              <label className="mb-4 flex items-start gap-3 rounded-xl bg-warn-bg p-4 text-sm text-warn">
                <input type="checkbox" className="mt-1" aria-label="Use draft questions" checked={drafts} onChange={(e) => setDrafts(e.target.checked)} />
                <span>
                  <span className="font-semibold">Use draft questions.</span> These are not yet checked by two reviewers. Good for
                  practice, but do not publish the results.
                </span>
              </label>
            )}
            <div className="grid gap-3 sm:grid-cols-2">
              {status.tasks.map((t) => (
                <label
                  key={t.name}
                  className={`flex gap-3 rounded-xl border p-4 transition-colors duration-150 ${
                    tasks.includes(t.name) ? "border-accent bg-info-bg" : "border-line hover:bg-surface-2"
                  }`}
                >
                  <input type="checkbox" className="mt-1 accent-[var(--accent)]" aria-label={`${taskLabel(t.name)}, ${count(t.name)} questions`} checked={tasks.includes(t.name)} onChange={() => toggleTask(t.name)} />
                  <span className="min-w-0">
                    <span className="block font-semibold">{taskLabel(t.name)}</span>
                    <span className="block text-xs text-muted">{count(t.name)} questions · <span className="font-mono">{t.name}</span></span>
                    <span className="mt-1 block text-xs text-muted">{t.description}</span>
                  </span>
                </label>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-6 lg:sticky lg:top-24 lg:self-start">
          <Card>
            <CardTitle>Options</CardTitle>
            <label className="block text-sm font-medium" htmlFor="limit">Questions per topic</label>
            <input id="limit" inputMode="numeric" className={`${inputClass} mt-2 w-full`} placeholder="all" value={limit} onChange={(e) => setLimit(e.target.value)} />
            <Hint>Start small (2) to try it out. Leave empty to ask every question. Fewer questions = faster and uses less of your free quota.</Hint>
            <label className="mt-5 block text-sm font-medium" htmlFor="max-tokens">Max answer length</label>
            <input id="max-tokens" inputMode="numeric" className={`${inputClass} mt-2 w-full`} value={maxTokens} onChange={(e) => setMaxTokens(e.target.value)} />
            <Hint>The longest answer the model may give, in tokens (a token is roughly ¾ of a word). 512 suits almost every model.</Hint>
            <div className="mt-5 rounded-xl bg-surface-2 p-4 text-sm">
              <p className="font-medium">Fixed for fairness</p>
              <p className="mt-1 text-xs text-muted">
                Temperature {status.settings.temperature} and seed {status.settings.seed} make answers as repeatable as possible.
                Every model gets the same values, so they cannot be changed here.
              </p>
            </div>
          </Card>
          <Card>
            <CardTitle>Ready?</CardTitle>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
              <dt className="text-muted">Model</dt>
              <dd className="break-all font-mono">{model ? `${provider}/${model}` : "not chosen"}</dd>
              <dt className="text-muted">Topics</dt>
              <dd>{tasks.length}</dd>
              <dt className="text-muted">Questions</dt>
              <dd>{tasks.length ? questions : 0}</dd>
            </dl>
            {submitError && <div className="mt-4"><ErrorBox message={submitError} /></div>}
            <button type="button" className={`${buttonPrimary} mt-5 w-full`} onClick={start} disabled={submitting}>
              <Play aria-hidden className="size-4" /> {submitting ? "Starting…" : "Start test"}
            </button>
            <Hint>Questions are sent one at a time to stay within free limits. You can leave the page while it runs.</Hint>
          </Card>
        </div>
      </div>
    </div>
  );
}
