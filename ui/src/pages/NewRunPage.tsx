import { CheckCircle2, KeyRound, Play, RefreshCw, Server } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Provider } from "../api";
import { Card, CardTitle, ErrorBox, Hint, InfoBox, Loading, PageTitle, buttonPrimary, buttonSecondary, inputClass } from "../components";
import { taskLabel, useLoad } from "../lib";

const GROUPS: { id: Provider["group"]; title: string; hint: string }[] = [
  { id: "free", title: "Free to start", hint: "Free keys with daily limits." },
  { id: "paid", title: "Paid APIs", hint: "Billed by the provider to your own account." },
  { id: "local", title: "On this computer", hint: "No key needed." },
  { id: "own", title: "Your own server", hint: "Any OpenAI-compatible address." },
];

const labelClass = "block text-sm font-medium text-text";

export function NewRunPage() {
  const { data: status, error, reload } = useLoad(api.status);
  const navigate = useNavigate();
  const [provider, setProvider] = useState("");
  const [models, setModels] = useState<string[] | null>(null);
  const [modelsAsOf, setModelsAsOf] = useState("");
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [picked, setPicked] = useState("");
  const [typed, setTyped] = useState("");
  const [tasks, setTasks] = useState<string[]>([]);
  const [drafts, setDrafts] = useState(false);
  const [limit, setLimit] = useState("2");
  const [maxTokens, setMaxTokens] = useState("512");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!status) return;
    if (!provider) {
      // Start on a provider the user has set up (key or server saved). Ollama is "ready"
      // without a key but may not be running (always the case in Colab), so it is never
      // the default; with nothing set up, start on the keyless practice model.
      const first = status.providers.find((p) => p.ready && p.group !== "local") ?? status.providers.find((p) => p.name === "mock");
      if (first) setProvider(first.name);
    }
    if (status.drafts_available && status.tasks.every((t) => t.items === 0)) setDrafts(true);
  }, [status, provider]);

  const current = status?.providers.find((p) => p.name === provider);

  const loadModels = () => {
    setModels(null);
    setModelsError(null);
    setPicked("");
    if (!current?.ready) return;
    api
      .models(provider)
      .then((r) => {
        setModels(r.models);
        setModelsAsOf(r.as_of);
      })
      .catch((e: Error) => setModelsError(e.message));
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(loadModels, [provider, current?.ready, current?.custom_url]);

  const shown = useMemo(
    () => (models ?? []).filter((m) => m.toLowerCase().includes(filter.toLowerCase())),
    [models, filter],
  );

  if (error) return <ErrorBox message={error} />;
  if (!status) return <Loading />;

  const model = typed.trim() || picked;
  const count = (name: string) => {
    const t = status.tasks.find((x) => x.name === name);
    return t ? (drafts ? t.draft_items : t.items) : 0;
  };
  const toggleTask = (name: string) => setTasks((ts) => (ts.includes(name) ? ts.filter((t) => t !== name) : [...ts, name]));
  const allTasks = status.tasks.map((t) => t.name);
  const limitNum = limit.trim() === "" ? null : Number(limit);
  const tokensNum = Number(maxTokens);
  const questions = tasks.reduce((a, t) => a + Math.min(count(t), limitNum ?? Infinity), 0);
  const problems: string[] = [];
  if (!current?.ready) problems.push("Finish setting up the provider in step 1.");
  if (!model) problems.push("Choose or type a model in step 2.");
  if (tasks.length === 0) problems.push("Select at least one topic in step 3.");
  if (tasks.some((t) => count(t) === 0)) problems.push("Some selected topics have no questions yet. Turn on draft questions or unselect them.");
  if (limitNum !== null && (!Number.isInteger(limitNum) || limitNum < 1)) problems.push("Questions per topic must be a whole number, 1 or more.");
  if (!Number.isInteger(tokensNum) || tokensNum < 1 || tokensNum > 8192) problems.push("Maximum answer length must be between 1 and 8192.");

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
    <div className="space-y-12">
      <PageTitle
        title="New test"
        sub="Choose any provider and model, using your own API key. Every model receives the same questions and settings, so results are comparable."
      />

      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-10">
          <Card>
            <CardTitle hint="Your key is used only for your tests and stays on this computer.">1. Provider</CardTitle>
            <div className="space-y-8">
              {GROUPS.map((g) => {
                const items = status.providers.filter((p) => p.group === g.id);
                if (items.length === 0) return null;
                return (
                  <fieldset key={g.id}>
                    <legend className="mb-3 flex items-baseline gap-3">
                      <span className="text-xs font-semibold uppercase tracking-wider text-muted">{g.title}</span>
                      <span className="text-xs text-muted">{g.hint}</span>
                    </legend>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {items.map((p) => (
                        <ProviderCard key={p.name} p={p} selected={provider === p.name} onSelect={() => setProvider(p.name)} />
                      ))}
                    </div>
                  </fieldset>
                );
              })}
            </div>
            {current && (
              <div className="mt-8 border-t border-line pt-8">
                {current.name === "custom" ? (
                  <CustomForm provider={current} onSaved={reload} />
                ) : current.needs_key && !current.key_set ? (
                  <KeyForm provider={current} onSaved={reload} />
                ) : (
                  <ReadyNote provider={current} onSaved={reload} />
                )}
              </div>
            )}
          </Card>

          <Card>
            <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-primary">2. Model</h2>
                <p className="mt-1.5 text-sm text-muted">Pick from the provider's live list, or type the exact model name.</p>
              </div>
              {current?.ready && (
                <button type="button" className={buttonSecondary} onClick={loadModels}>
                  <RefreshCw aria-hidden className="size-4" /> Refresh list
                </button>
              )}
            </div>
            {!current?.ready && <p className="text-sm text-muted">Set up the provider in step 1 first.</p>}
            {current?.ready && (
              <div className="grid gap-8 md:grid-cols-2">
                <div>
                  <label className={labelClass} htmlFor="model-filter">From the list</label>
                  {modelsError && <div className="mt-2"><ErrorBox message={`Could not load the list: ${modelsError}`} /></div>}
                  {!models && !modelsError && <div className="mt-3"><Loading label="Loading models" /></div>}
                  {models && models.length === 0 && (
                    <p className="mt-2 text-sm text-muted">
                      {provider === "ollama" ? "No models downloaded yet. Run `ollama pull <model>` in a terminal, then refresh." : "The provider returned an empty list. Type the model name instead."}
                    </p>
                  )}
                  {models && models.length > 0 && (
                    <>
                      <input id="model-filter" className={`${inputClass} mt-2 w-full`} placeholder="Search models" value={filter} onChange={(e) => setFilter(e.target.value)} />
                      <label className="sr-only" htmlFor="model-select">Model list</label>
                      <select id="model-select" size={8} className={`${inputClass} mt-2 h-auto w-full py-2 font-mono`} value={picked} onChange={(e) => { setPicked(e.target.value); setTyped(""); }}>
                        <option value="" disabled>Select a model</option>
                        {shown.map((m) => <option key={m} value={m}>{m}</option>)}
                      </select>
                      <Hint>{models.length} models available{modelsAsOf ? ` (as of ${modelsAsOf})` : ""}.</Hint>
                    </>
                  )}
                </div>
                <div>
                  <label className={labelClass} htmlFor="model-typed">Or type a model name</label>
                  <input id="model-typed" className={`${inputClass} mt-2 w-full font-mono`} placeholder="e.g. gpt-4o-mini" spellCheck={false} value={typed} onChange={(e) => setTyped(e.target.value)} />
                  <Hint>Use this when a model is not in the list, or for your own server. The name must match the provider's model id exactly.</Hint>
                  <div className="mt-6 rounded-xl bg-surface-2 p-4 text-sm">
                    <span className="text-muted">Selected model</span>
                    <p className="mt-1 break-all font-mono font-medium">{model ? `${provider}/${model}` : "None yet"}</p>
                  </div>
                </div>
              </div>
            )}
          </Card>

          <Card>
            <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-primary">3. Topics</h2>
                <p className="mt-1.5 text-sm text-muted">Each topic is a short set of questions of one kind.</p>
              </div>
              <button type="button" className={buttonSecondary} onClick={() => setTasks(tasks.length === allTasks.length ? [] : allTasks)}>
                {tasks.length === allTasks.length ? "Clear all" : "Select all"}
              </button>
            </div>
            {status.drafts_available && (
              <label className="mb-6 flex items-start gap-3 rounded-xl bg-warn-bg p-4 text-sm text-warn">
                <input type="checkbox" className="mt-1" aria-label="Use draft questions" checked={drafts} onChange={(e) => setDrafts(e.target.checked)} />
                <span><span className="font-semibold">Use draft questions.</span> Not yet approved by two reviewers. Suitable for practice; results must not be published.</span>
              </label>
            )}
            <div className="grid gap-3 sm:grid-cols-2">
              {status.tasks.map((t) => (
                <label key={t.name} className={`flex gap-3 rounded-xl border p-4 transition-colors duration-150 ${tasks.includes(t.name) ? "border-accent bg-info-bg" : "border-line hover:bg-surface-2"}`}>
                  <input type="checkbox" className="mt-1 accent-[var(--accent)]" aria-label={`${taskLabel(t.name)}, ${count(t.name)} questions`} checked={tasks.includes(t.name)} onChange={() => toggleTask(t.name)} />
                  <span className="min-w-0">
                    <span className="block font-semibold">{taskLabel(t.name)}</span>
                    <span className="mt-0.5 block text-xs text-muted">{count(t.name)} questions</span>
                  </span>
                </label>
              ))}
            </div>
          </Card>
        </div>

        <aside className="space-y-6 lg:sticky lg:top-24 lg:self-start">
          <Card>
            <CardTitle>Summary</CardTitle>
            <dl className="space-y-3 text-sm">
              <div><dt className="text-muted">Provider</dt><dd className="font-medium">{current?.label ?? "None"}</dd></div>
              <div><dt className="text-muted">Model</dt><dd className="break-all font-mono">{model || "None"}</dd></div>
              <div><dt className="text-muted">Topics</dt><dd>{tasks.length} selected · {tasks.length ? questions : 0} questions</dd></div>
            </dl>
            <div className="mt-6 space-y-5 border-t border-line pt-6">
              <div>
                <label className={labelClass} htmlFor="limit">Questions per topic</label>
                <input id="limit" inputMode="numeric" className={`${inputClass} mt-2 w-full`} placeholder="all" value={limit} onChange={(e) => setLimit(e.target.value)} />
                <Hint>Start with 2. Leave empty to use every question.</Hint>
              </div>
              <div>
                <label className={labelClass} htmlFor="max-tokens">Maximum answer length</label>
                <input id="max-tokens" inputMode="numeric" className={`${inputClass} mt-2 w-full`} value={maxTokens} onChange={(e) => setMaxTokens(e.target.value)} />
                <Hint>In tokens (about ¾ of a word each). 512 suits most models.</Hint>
              </div>
              <p className="rounded-xl bg-surface-2 p-4 text-xs leading-relaxed text-muted">
                Temperature {status.settings.temperature} and seed {status.settings.seed} are fixed for every model. If a provider rejects a setting, the result records it.
              </p>
            </div>
            {submitError && <div className="mt-6"><ErrorBox message={submitError} /></div>}
            <button type="button" className={`${buttonPrimary} mt-6 w-full`} onClick={start} disabled={submitting}>
              <Play aria-hidden className="size-4" /> {submitting ? "Starting…" : "Start test"}
            </button>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function ProviderCard({ p, selected, onSelect }: { p: Provider; selected: boolean; onSelect: () => void }) {
  const status = p.ready ? "Ready" : p.name === "custom" ? "Address needed" : "Key needed";
  return (
    <label className={`flex h-full gap-3 rounded-xl border p-4 transition-colors duration-150 ${selected ? "border-accent bg-info-bg" : "border-line hover:bg-surface-2"}`}>
      <input type="radio" name="provider" className="mt-1 accent-[var(--accent)]" aria-label={`${p.label}, ${status}`} checked={selected} onChange={onSelect} />
      <span className="min-w-0 flex-1">
        <span className="flex flex-wrap items-center gap-2">
          <span className="font-semibold">{p.label}</span>
          <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${p.ready ? "bg-info-bg text-info" : "bg-surface-2 text-muted"}`}>{status}</span>
          {!p.verified && <span className="rounded-md border border-line px-2 py-0.5 text-[11px] text-muted">Beta</span>}
        </span>
        <span className="mt-1 block text-xs leading-relaxed text-muted">{p.description}</span>
      </span>
    </label>
  );
}

function ReadyNote({ provider, onSaved }: { provider: Provider; onSaved: () => void }) {
  const [replacing, setReplacing] = useState(false);
  if (replacing && provider.needs_key) return <KeyForm provider={provider} onSaved={() => { setReplacing(false); onSaved(); }} />;
  return (
    <div className="flex flex-wrap items-center justify-between gap-4">
      <p className="flex items-center gap-2 text-sm">
        <CheckCircle2 aria-hidden className="size-5 text-info" />
        <span><span className="font-semibold">{provider.label}</span> is ready{provider.needs_key ? " with your saved key." : "."}</span>
      </p>
      {provider.needs_key && (
        <button type="button" className={buttonSecondary} onClick={() => setReplacing(true)}>
          <KeyRound aria-hidden className="size-4" /> Replace key
        </button>
      )}
    </div>
  );
}

function KeyForm({ provider, onSaved }: { provider: Provider; onSaved: () => void }) {
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const save = async () => {
    setProblem(null);
    if (!value.trim()) {
      setProblem("Paste your key first.");
      return;
    }
    setSaving(true);
    try {
      await api.saveKey(provider.name, value);
      setValue("");
      onSaved();
    } catch (e) {
      setProblem(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };
  return (
    <div>
      <p className="flex items-center gap-2 font-semibold text-primary"><KeyRound aria-hidden className="size-4" /> Your {provider.label} API key</p>
      <p className="mt-1.5 text-sm text-muted">
        {provider.signup_url ? (
          <>Create a key at{" "}<a className="font-medium text-link underline" href={provider.signup_url} target="_blank" rel="noreferrer">{provider.signup_url.replace("https://", "")}</a>, then paste it below.</>
        ) : "Paste your key below."}
      </p>
      <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={(e) => { e.preventDefault(); void save(); }}>
        <label className="sr-only" htmlFor="api-key">{provider.label} API key</label>
        <input id="api-key" type="password" autoComplete="off" spellCheck={false} className={`${inputClass} w-full font-mono`} placeholder="Paste key" value={value} onChange={(e) => { setValue(e.target.value); setProblem(null); }} />
        <button type="submit" className={buttonPrimary} disabled={saving}>{saving ? "Saving…" : "Save key"}</button>
      </form>
      {problem && <p className="mt-2 text-sm text-danger">{problem}</p>}
      <Hint>Stored only on this computer (in your home folder, .touchstone/.env), never shown again, and sent only to {provider.label}.</Hint>
    </div>
  );
}

function CustomForm({ provider, onSaved }: { provider: Provider; onSaved: () => void }) {
  const [url, setUrl] = useState(provider.custom_url ?? "");
  const [key, setKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const save = async () => {
    setProblem(null);
    setSaved(false);
    if (!/^https?:\/\/\S+$/.test(url.trim())) {
      setProblem("Enter an address that starts with http:// or https://");
      return;
    }
    setSaving(true);
    try {
      await api.saveCustom(url.trim(), key.trim() || null);
      setKey("");
      setSaved(true);
      onSaved();
    } catch (e) {
      setProblem(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };
  return (
    <div>
      <p className="flex items-center gap-2 font-semibold text-primary"><Server aria-hidden className="size-4" /> Your own server</p>
      <p className="mt-1.5 text-sm text-muted">
        Works with any service that offers an OpenAI-compatible API: a company endpoint, LM Studio, vLLM, or another provider. The address usually ends in <code className="font-mono">/v1</code>.
      </p>
      <form className="mt-5 grid gap-4" onSubmit={(e) => { e.preventDefault(); void save(); }}>
        <div>
          <label className={labelClass} htmlFor="custom-url">Server address</label>
          <input id="custom-url" className={`${inputClass} mt-2 w-full font-mono`} placeholder="https://api.example.com/v1" spellCheck={false} value={url} onChange={(e) => { setUrl(e.target.value); setProblem(null); setSaved(false); }} />
        </div>
        <div>
          <label className={labelClass} htmlFor="custom-key">API key <span className="font-normal text-muted">(optional)</span></label>
          <input id="custom-key" type="password" autoComplete="off" spellCheck={false} className={`${inputClass} mt-2 w-full font-mono`} placeholder={provider.custom_url ? "Leave empty to keep the saved key" : "Paste key, if the server needs one"} value={key} onChange={(e) => setKey(e.target.value)} />
        </div>
        <div className="flex items-center gap-4">
          <button type="submit" className={buttonPrimary} disabled={saving}>{saving ? "Saving…" : "Save server"}</button>
          {saved && <span className="text-sm text-info">Saved.</span>}
        </div>
      </form>
      {problem && <p className="mt-2 text-sm text-danger">{problem}</p>}
      <Hint>Then pick a model in step 2. If the server does not list its models, type the model name.</Hint>
      {provider.custom_url && <div className="mt-4"><InfoBox>Currently saved: <span className="font-mono">{provider.custom_url}</span></InfoBox></div>}
    </div>
  );
}
