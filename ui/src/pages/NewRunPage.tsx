import { KeyRound, Play, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Provider } from "../api";
import { Card, ErrorBox, Loading, PageTitle, buttonPrimary, buttonSecondary, inputClass } from "../components";
import { useLoad } from "../lib";

const KEY_VARS: Record<string, string> = {
  groq: "GROQ_API_KEY",
  gemini: "GEMINI_API_KEY",
  openrouter: "OPENROUTER_API_KEY",
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
  const [limit, setLimit] = useState("");
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
  const limitNum = limit.trim() === "" ? null : Number(limit);
  const tokensNum = Number(maxTokens);
  const problems: string[] = [];
  if (!model) problems.push("Choose a model.");
  if (tasks.length === 0) problems.push("Choose at least one task.");
  if (tasks.some((t) => count(t) === 0)) problems.push("Some chosen tasks have no items yet.");
  if (limitNum !== null && (!Number.isInteger(limitNum) || limitNum < 1)) problems.push("Limit must be a whole number of 1 or more.");
  if (!Number.isInteger(tokensNum) || tokensNum < 1 || tokensNum > 8192) problems.push("Max tokens must be between 1 and 8192.");

  const start = async () => {
    setSubmitError(null);
    if (problems.length) {
      setSubmitError(problems.join(" "));
      return;
    }
    setSubmitting(true);
    try {
      const { job_id } = await api.startJob({
        model: `${provider}/${model}`,
        tasks,
        limit: limitNum,
        max_tokens: tokensNum,
        drafts,
      });
      navigate(`/jobs/${job_id}`);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : String(e));
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageTitle title="New run" sub="Every model gets the same fixed settings, so results stay comparable." />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          <Card>
            <h2 className="mb-3 font-medium">1. Provider</h2>
            <div className="grid gap-2 sm:grid-cols-2" role="radiogroup" aria-label="Provider">
              {status.providers.map((p) => (
                <label
                  key={p.name}
                  className={`flex items-center gap-3 rounded-lg border px-3 py-2 text-sm ${
                    provider === p.name ? "border-primary" : "border-line"
                  }`}
                >
                  <input
                    type="radio"
                    name="provider"
                    aria-label={`${p.name}, ${p.needs_key ? (p.key_set ? "key set" : "no key") : "no key needed"}`}
                    checked={provider === p.name}
                    onChange={() => setProvider(p.name)}
                  />
                  <span className="font-medium">{p.name === "mock" ? "mock (offline demo)" : p.name}</span>
                  <span className="ml-auto text-xs text-muted">
                    {p.needs_key ? (p.key_set ? "key set" : "no key") : "no key needed"}
                  </span>
                </label>
              ))}
            </div>
            {current && !usable(current) && (
              <p className="mt-3 flex gap-2 rounded-lg bg-surface-2 p-3 text-sm">
                <KeyRound aria-hidden className="mt-0.5 size-4 shrink-0" />
                <span>
                  Add <code className="font-mono">{KEY_VARS[current.name] ?? "the API key"}=…</code> to the{" "}
                  <code className="font-mono">.env</code> file in the folder where you started touchstone, then restart{" "}
                  <code className="font-mono">touchstone ui</code>. Keys never leave your computer except to that provider.
                </span>
              </p>
            )}
          </Card>

          {current && usable(current) && (
            <Card>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-medium">2. Model</h2>
                <button type="button" className={buttonSecondary} onClick={loadModels}>
                  <RefreshCw aria-hidden className="size-4" /> Refresh list
                </button>
              </div>
              {modelsError && <ErrorBox message={modelsError} />}
              {!models && !modelsError && <Loading label="Loading models from the provider" />}
              {models && (
                <>
                  <label className="mb-1 block text-sm text-muted" htmlFor="model-filter">
                    Filter {models.length} models (live list, {modelsAsOf})
                  </label>
                  <input id="model-filter" className={inputClass} placeholder="flash" value={filter} onChange={(e) => setFilter(e.target.value)} />
                  <label className="sr-only" htmlFor="model-select">Model</label>
                  <select id="model-select" size={8} className={`${inputClass} mt-2 font-mono`} value={model} onChange={(e) => setModel(e.target.value)}>
                    <option value="" disabled>Choose a model</option>
                    {shown.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  {provider === "openrouter" && (
                    <p className="mt-2 text-xs text-muted">Free models end in “:free” and are often busy (HTTP 429).</p>
                  )}
                </>
              )}
            </Card>
          )}

          <Card>
            <h2 className="mb-3 font-medium">3. Tasks</h2>
            {status.drafts_available && (
              <label className="mb-3 flex items-start gap-2 rounded-lg bg-warn-bg p-3 text-sm text-warn">
                <input
                  type="checkbox"
                  className="mt-1"
                  aria-label="Use draft items (unreviewed)"
                  checked={drafts}
                  onChange={(e) => setDrafts(e.target.checked)}
                />
                <span>Use draft items (unreviewed). For trying things out only; results are marked and must not be published.</span>
              </label>
            )}
            <div className="space-y-1">
              {status.tasks.map((t) => (
                <label key={t.name} className="flex items-start gap-3 rounded-lg px-2 py-2 hover:bg-surface-2">
                  <input
                    type="checkbox"
                    className="mt-1"
                    aria-label={`${t.name}, ${count(t.name)} items`}
                    checked={tasks.includes(t.name)}
                    onChange={() => toggleTask(t.name)}
                  />
                  <span className="min-w-0">
                    <span className="font-mono text-[13px]">{t.name}</span>
                    <span className="ml-2 text-xs text-muted">{count(t.name)} items</span>
                    <span className="block text-sm text-muted">{t.description}</span>
                  </span>
                </label>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <h2 className="mb-3 font-medium">Settings</h2>
            <label className="block text-sm" htmlFor="limit">Items per task (empty = all)</label>
            <input id="limit" inputMode="numeric" className={`${inputClass} mt-1`} placeholder="5" value={limit} onChange={(e) => setLimit(e.target.value)} />
            <label className="mt-3 block text-sm" htmlFor="max-tokens">Max reply tokens</label>
            <input id="max-tokens" inputMode="numeric" className={`${inputClass} mt-1`} value={maxTokens} onChange={(e) => setMaxTokens(e.target.value)} />
            <dl className="mt-4 grid grid-cols-2 gap-y-1 text-sm">
              <dt className="text-muted">temperature</dt><dd className="tabular text-right">{status.settings.temperature} (fixed)</dd>
              <dt className="text-muted">seed</dt><dd className="tabular text-right">{status.settings.seed} (fixed)</dd>
              <dt className="text-muted">top_p</dt><dd className="tabular text-right">{status.settings.top_p} (fixed)</dd>
            </dl>
          </Card>
          <Card>
            <p className="mb-3 text-sm text-muted">
              {model ? <>Model: <span className="font-mono text-text">{provider}/{model}</span></> : "No model chosen yet."}
              <br />
              {tasks.length} task(s) selected. Items run one at a time to respect free-tier limits.
            </p>
            {submitError && <div className="mb-3"><ErrorBox message={submitError} /></div>}
            <button type="button" className={`${buttonPrimary} w-full justify-center`} onClick={start} disabled={submitting}>
              <Play aria-hidden className="size-4" /> {submitting ? "Starting…" : "Start run"}
            </button>
          </Card>
        </div>
      </div>
    </>
  );
}
