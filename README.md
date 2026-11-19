# touchstone

**Small, reproducible tests for LLMs in Hindi and Hinglish. One command, one clear report.**

A touchstone is the dark stone jewellers use to test gold. touchstone does the same for language models in Hindi and Hinglish. Think of it as a pytest for Indic LLMs: point it at a model, pick tasks, and get a score table, a shareable HTML report, and every prompt and reply saved for anyone to check.

> **Status: pre-release (0.1.0.dev).** Not on PyPI yet. The dataset is still being reviewed, so no official results are published.

<!-- TODO: add a short GIF of `touchstone run` and the web UI here, e.g. docs/demo.gif -->
> *Demo GIF coming soon.*

## 30-second quickstart

```bash
pip install "touchstone-llm[ui]"          # after the first release; until then: pip install -e ".[ui]"
cp .env.example .env                # add one free API key (Gemini, Groq or OpenRouter)
touchstone list-models groq            # model ids change; always pick from the live list
touchstone run --model groq/<model-id> --tasks hinglish_understanding,translation_hi_en
touchstone ui                          # optional: local web UI at http://127.0.0.1:7860
```

No key? `touchstone run --model mock/fixed --tasks all` runs offline with a fake model.

Every run prints a table and saves three files in `runs/`: the full result as JSON, a Markdown summary, and a self-contained HTML report.

## What it tests (v1)

| Task | What the model does | Scoring |
|---|---|---|
| `hindi_comprehension` | Reads a short Hindi passage, answers a multiple-choice question | exact option match |
| `hinglish_understanding` | Understands Roman-script Hindi-English chat text, including sarcasm | exact option match |
| `translation_hi_en` | Translates Hindi into English | chrF against 1-2 references |
| `codemixed_instructions` | Follows Hinglish instructions with checkable formats | rule checks, all must pass |
| `hindi_reasoning` | Solves arithmetic and logic word problems in Hindi | numeric exact match |
| `cultural_context` | Answers neutral, factual questions on festivals, food, geography and institutions | exact option match |

No LLM is used as a judge. Answers that can't be parsed count as wrong and are reported separately as "unparsed".

## How results stay fair and reproducible

- **Same settings for every model:** temperature 0, seed 42, top_p 1, and the same prompt templates. The CLI does not let you change temperature or seed.
- **Everything is recorded:** the model you asked for, the model id the provider actually used, the date, settings, number of items, touchstone version, and every exact prompt and reply.
- **One-command reproduction:** `touchstone reproduce runs/<result>.json` reruns with identical config and reports whether prompts and settings match.
- **Resumable on free tiers:** replies are cached locally, so a run stopped by a rate limit continues where it left off.
- **Neutral wording:** reports show numbers, sample sizes and limitations. touchstone never declares a "best" model.

## Results

No official results yet. They will be published here only after every item has been reviewed by two people, with the date, model ids, settings, n and prompts for each run.

## Limitations

Please read [LIMITATIONS.md](LIMITATIONS.md). In short:

- The dataset is small (about 25 items per task). Small differences are often noise.
- **Hindi does not represent all of India.** Other Indian languages and many dialects are not covered.
- Hinglish has no standard spelling, so rule-based scoring can miss valid answers.
- chrF is a rough translation signal. API models can change behind the same name.

## Data, licenses and safety

- Code: [Apache-2.0](LICENSE). Dataset items: CC-BY-4.0, written for this project. Nothing is copied from exams, books or websites. Some first drafts had AI assistance; every item is checked by its author and approved by **at least two other people** before it is scored. See [DATASETS.md](DATASETS.md).
- Cultural items stay neutral and factual: no religion comparisons, caste, politics, or regional stereotypes.
- API keys live only in your local `.env`. touchstone never logs them and collects no telemetry. The web UI only listens on `127.0.0.1`.

## Related work

touchstone is a small, laptop-first tool, not a replacement for these larger efforts. It shares no data or code with them.

- **MILU** (AI4Bharat and IBM Research India): a multi-task Indic language understanding benchmark with multiple-choice questions across 11 Indic languages. Verma et al., NAACL 2025. [arXiv:2411.02538](https://arxiv.org/abs/2411.02538)
- **IndicGenBench** (Google Research India): evaluates LLM generation (summarization, translation, QA) across 29 Indic languages. Singh et al., ACL 2024. [arXiv:2404.16816](https://arxiv.org/abs/2404.16816) · [code and data](https://github.com/google-research-datasets/indic-gen-bench)
- **indic_eval** (GitHub: adithya-s-k): an evaluation suite for Indic LLMs built on Hugging Face LightEval, with translated versions of ARC, HellaSwag, BoolQ and MMLU. [github.com/adithya-s-k/indic_eval](https://github.com/adithya-s-k/indic_eval). (This project was first planned as "indic-eval"; it was renamed so the two are not confused.)
- **HinglishEval**: tests code-generation models on Hinglish programming prompts. COMPUTE 2024. [github.com/mrigankpawagi/HinglishEval](https://github.com/mrigankpawagi/HinglishEval)

How touchstone differs: it focuses on Hindi and Hinglish everyday tasks, uses only original reviewed items, runs on free APIs or tiny local models, and ships a CLI plus a local UI for reproducible runs.

## How to cite

If you use touchstone, please cite it using [CITATION.cff](CITATION.cff) (GitHub shows a "Cite this repository" button).

## Contributing

Contributions are welcome, especially new items and reviews from fluent Hindi and Hinglish speakers. See [CONTRIBUTING.md](CONTRIBUTING.md), the [review guide](datasets/README.md), and the [Code of Conduct](CODE_OF_CONDUCT.md).
