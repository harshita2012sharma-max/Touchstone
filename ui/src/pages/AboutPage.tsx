import { Link } from "react-router-dom";
import { api } from "../api";
import { Card, CardTitle, Glossary, PageTitle, StepCard, buttonPrimary } from "../components";
import { TASK_LABELS, useLoad } from "../lib";

export function AboutPage() {
  const { data: status } = useLoad(api.status);
  return (
    <div className="space-y-8">
      <PageTitle
        title="Help"
        sub={`What touchstone is, how to use it, and what the results mean.${status ? ` Version ${status.version}.` : ""}`}
        action={<Link to="/new" className={buttonPrimary}>Start a test</Link>}
      />

      <Card>
        <CardTitle>What is touchstone?</CardTitle>
        <p className="text-sm">
          A touchstone is the dark stone jewellers use to test gold. This tool does the same for AI models: it gives a
          model a short exam in Hindi and Hinglish, checks every answer with fixed rules, and shows the result. Every
          model gets the same questions and settings, so results are fair.
        </p>
      </Card>

      <section aria-label="How to use it" className="grid gap-6 md:grid-cols-3">
        <StepCard n={1} title="Start a test">Open “New test”, pick a provider and a model, and tick some topics.</StepCard>
        <StepCard n={2} title="Wait a minute">The model answers each question. A progress bar shows how far it has got.</StepCard>
        <StepCard n={3} title="Read the result">See the overall score, a score per topic, and every answer. Compare tests side by side.</StepCard>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardTitle hint="Each topic is a small set of questions of one kind.">The six topics</CardTitle>
          <ul className="space-y-2 text-sm">
            {Object.entries(TASK_LABELS).map(([id, label]) => (
              <li key={id} className="flex justify-between gap-4">
                <span className="font-medium">{label}</span>
                <span className="font-mono text-xs text-muted">{id}</span>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <CardTitle>Privacy and data</CardTitle>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            <li>This page runs only on your computer and collects nothing about you.</li>
            <li>Questions go only to the model provider you choose.</li>
            <li>API keys are read from your local <code className="font-mono">.env</code> file and never shown here.</li>
            <li>Questions are written for this project (CC-BY-4.0) and approved by two reviewers before they count.</li>
          </ul>
        </Card>
      </div>

      <Card>
        <CardTitle hint="What the words and numbers in the results mean.">Words you will see</CardTitle>
        <Glossary />
      </Card>

      <Card>
        <CardTitle>Limits to keep in mind</CardTitle>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          <li>Only a few questions per topic, so small differences are often just luck.</li>
          <li>Hindi does not represent all of India; other Indian languages are not tested.</li>
          <li>Hinglish spelling varies, so a correct answer can sometimes be marked wrong.</li>
          <li>Online models can change without a new name.</li>
        </ul>
      </Card>
    </div>
  );
}
