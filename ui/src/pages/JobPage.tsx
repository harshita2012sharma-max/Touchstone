import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, type Job } from "../api";
import { Card, ErrorBox, Hint, Loading, PageTitle, buttonSecondary } from "../components";
import { taskLabel } from "../lib";

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

  if (lost) return <ErrorBox message={`Lost contact with this test: ${lost}`} />;
  if (!job) return <Loading label="Connecting" />;

  const entries = Object.entries(job.progress);
  const done = entries.reduce((a, [, p]) => a + p.done, 0);
  const total = entries.reduce((a, [, p]) => a + p.total, 0);
  return (
    <div className="space-y-12">
      <PageTitle
        title={job.state === "failed" ? "The test stopped" : "Test in progress"}
        sub={job.state === "failed"
          ? "Something went wrong. Answers received so far are saved, so starting the same test again continues from here."
          : `${job.model} is answering the questions one by one. The result opens by itself when it finishes.`}
      />
      <Card>
        {total > 0 && (
          <p className="mb-5 text-sm font-medium">{done} of {total} questions answered</p>
        )}
        {entries.length === 0 && job.state === "running" && <Loading label="Preparing the questions" />}
        <ul className="space-y-5" aria-live="polite">
          {entries.map(([task, p]) => (
            <li key={task}>
              <div className="mb-2 flex justify-between text-sm">
                <span className="font-medium">{taskLabel(task)}</span>
                <span className="tabular text-muted">{p.done} / {p.total}</span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-label={taskLabel(task)} aria-valuemin={0} aria-valuemax={p.total} aria-valuenow={p.done}>
                <div className="h-full rounded-full bg-accent transition-[width] duration-300" style={{ width: `${(p.done / Math.max(p.total, 1)) * 100}%` }} />
              </div>
            </li>
          ))}
        </ul>
        {job.state === "running" && <Hint>You can leave this page; the test keeps running and appears under Results.</Hint>}
      </Card>
      {job.state === "failed" && job.error && (
        <div className="space-y-4">
          <ErrorBox message={job.error} />
          <Link to="/new" className={buttonSecondary}>
            <ArrowLeft aria-hidden className="size-4" /> Back to new test
          </Link>
        </div>
      )}
    </div>
  );
}
