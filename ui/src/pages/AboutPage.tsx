import { Card, PageTitle } from "../components";
import { useLoad } from "../lib";
import { api } from "../api";

export function AboutPage() {
  const { data: status } = useLoad(api.status);
  return (
    <>
      <PageTitle title="About touchstone" sub={status ? `Version ${status.version}` : undefined} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-2 font-medium">What it is</h2>
          <p className="text-sm">
            A touchstone (<span lang="hi">कसौटी</span>, kasauti) is the dark stone used to test gold. This tool runs small,
            reproducible tests of language models in Hindi and Hinglish, with fixed settings (temperature 0,
            seed 42) for every model, and saves every prompt and reply.
          </p>
        </Card>
        <Card>
          <h2 className="mb-2 font-medium">Limitations</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            <li>The dataset is small, so small differences are often noise.</li>
            <li>Hindi does not represent all of India; other languages and dialects are not covered.</li>
            <li>Hinglish has no standard spelling, so rule-based scoring is imperfect.</li>
            <li>Translation scores (chrF) are a rough signal.</li>
            <li>API models can change behind the same name.</li>
          </ul>
        </Card>
        <Card>
          <h2 className="mb-2 font-medium">Data and licenses</h2>
          <p className="text-sm">
            Code: Apache-2.0. Dataset items are written for this project (CC-BY-4.0) and each is approved by at
            least two reviewers other than its author before it is scored. Fonts: Noto Sans, Noto Sans
            Devanagari and Fira Code (SIL Open Font License).
          </p>
        </Card>
        <Card>
          <h2 className="mb-2 font-medium">Privacy</h2>
          <p className="text-sm">
            This page runs only on your computer (127.0.0.1). touchstone collects no telemetry. Prompts go only to
            the model provider you choose, and API keys are read from your local <code className="font-mono">.env</code> file
            and never shown here.
          </p>
        </Card>
      </div>
    </>
  );
}
