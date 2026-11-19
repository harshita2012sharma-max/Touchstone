import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, type Job } from "../api";
import { Card, ErrorBox, Loading, PageTitle, buttonSecondary } from "../components";

export function JobPage() {
  const { jobId = "" } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [lost, setLost] = useState<string | null>(null);

  useEffect(() => {
    const source = new EventSource(api.jobEventsUrl(jobId));
    source.onmessage = (event) => {
      const next = JSON.parse(event.data) as Job;
      setJob(next);
      if (next.state !== "running") source.close();
      if (next.state === "done" && next.run_id) navigate(`/runs/${encodeURIComponent(next.run_id)}`, { replace: true });
    };
    source.onerror = () => {
      source.close();
      api.job(jobId).then(setJob).catch((e: Error) => setLost(e.message));
    };
    return () => source.close();
  }, [jobId, navigate]);

  if (lost) return <ErrorBox message={`Lost contact with this run: ${lost}`} />;
  if (!job) return <Loading label="Connecting" />;

  const entries = Object.entries(job.progress);
  return (
    <>
      <PageTitle title={job.state === "failed" ? "Run stopped" : "Running"} sub={job.model} />
      <Card>
        {entries.length === 0 && job.state === "running" && <Loading label="Preparing tasks" />}
        <ul className="space-y-3" aria-live="polite">
          {entries.map(([task, p]) => (
            <li key={task}>
              <div className="mb-1 flex justify-between text-sm">
                <span className="font-mono text-[13px]">{task}</span>
                <span className="tabular text-muted">{p.done} / {p.total}</span>
              </div>
              <div className="h-2 rounded-sm bg-surface-2" role="progressbar" aria-label={task} aria-valuemin={0} aria-valuemax={p.total} aria-valuenow={p.done}>
                <div className="h-full rounded-sm bg-series-1 transition-[width] duration-200" style={{ width: `${(p.done / Math.max(p.total, 1)) * 100}%` }} />
              </div>
            </li>
          ))}
        </ul>
        {job.state === "running" && (
          <p className="mt-4 text-xs text-muted">
            You can leave this page; the run continues and appears under Runs when finished.
          </p>
        )}
      </Card>
      {job.state === "failed" && job.error && (
        <div className="mt-4 space-y-3">
          <ErrorBox message={job.error} />
          <Link to="/new" className={buttonSecondary}>
            <ArrowLeft aria-hidden className="size-4" /> Back to new run
          </Link>
        </div>
      )}
    </>
  );
}
