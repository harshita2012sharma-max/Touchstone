// Typed client for the local touchstone API (see src/touchstone_llm/server/app.py).

export interface Provider {
  name: string;
  needs_key: boolean;
  key_set: boolean;
  signup_url: string | null;
}

export interface TaskInfo {
  name: string;
  version: string;
  description: string;
  items: number;
  draft_items: number;
}

export interface Settings {
  temperature: number;
  top_p: number;
  max_tokens: number;
  seed: number;
}

export interface Status {
  version: string;
  providers: Provider[];
  tasks: TaskInfo[];
  settings: Settings;
  drafts_available: boolean;
}

export interface TaskSummary {
  task: string;
  n: number;
  score: number;
  unparsed_rate: number;
}

export interface RunSummary {
  run_id: string;
  model: string;
  provider_model_id: string | null;
  started_at: string;
  allow_unreviewed: boolean;
  settings: Settings;
  total_n: number;
  mean_score: number;
  tasks: TaskSummary[];
}

export interface Sample {
  sample_id: string;
  prompt: string;
  output: string;
  expected: string | string[];
  score: number;
  parsed: string | null;
  unparsed: boolean;
  latency_ms: number | null;
}

export interface TaskResult extends TaskSummary {
  task_version: string;
  prompt_template: string;
  errors: number;
  samples: Sample[];
}

export interface RunResult {
  metadata: {
    run_id: string;
    tool_version: string;
    started_at: string;
    finished_at: string | null;
    provider_model_id: string | null;
    python_version: string;
    platform: string;
    git_sha: string | null;
  };
  config: {
    model: string;
    tasks: string[];
    settings: Settings;
    limit: number | null;
    allow_unreviewed: boolean;
  };
  tasks: TaskResult[];
}

export interface Job {
  job_id: string;
  model: string;
  state: "running" | "done" | "failed";
  progress: Record<string, { done: number; total: number }>;
  run_id: string | null;
  error: string | null;
}

export interface JobRequest {
  model: string;
  tasks: string[];
  limit: number | null;
  max_tokens: number;
  drafts: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // keep the generic message
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export const api = {
  status: () => request<Status>("/api/status"),
  models: (provider: string) =>
    request<{ provider: string; models: string[]; as_of: string }>(
      `/api/models/${encodeURIComponent(provider)}`,
    ),
  runs: () => request<{ runs: RunSummary[] }>("/api/runs").then((r) => r.runs),
  run: (id: string) => request<RunResult>(`/api/runs/${encodeURIComponent(id)}`),
  startJob: (body: JobRequest) =>
    request<{ job_id: string }>("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  saveKey: (provider: string, key: string) =>
    request<{ provider: string; key_set: boolean }>("/api/keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, key }),
    }),
  job: (id: string) => request<Job>(`/api/jobs/${encodeURIComponent(id)}`),
  reportUrl: (id: string) => `/api/runs/${encodeURIComponent(id)}/report`,
  jobEventsUrl: (id: string) => `/api/jobs/${encodeURIComponent(id)}/events`,
};
