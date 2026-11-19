# kasauti

**A touchstone for LLMs in Hindi and Hinglish.** Run small, reproducible evals from one command and get a clear report.

> Status: early development (pre-alpha). Nothing is published on PyPI yet, and the commands below are planned, not working.

*Kasauti* (कसौटी) is the touchstone used to test the purity of gold.

## Planned quickstart

```bash
pip install kasauti
kasauti list-models groq
kasauti run --model groq/<model-id> --tasks hinglish_understanding,translation_hi_en
```

<!-- TODO: demo GIF -->

## What it tests (v1)

1. Hindi comprehension
2. Hinglish (code-mixed) understanding
3. Hindi → English translation
4. Code-mixed instruction following
5. Hindi reasoning
6. Indian cultural context (neutral, factual questions only)

## Results

None yet. Every published result will list the model id, test date, settings, number of samples and the exact prompts.

## Limitations

See [LIMITATIONS.md](LIMITATIONS.md). In short: the dataset is small, Hindi does not represent all of India, and scoring of code-mixed text is imperfect.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Code: [Apache-2.0](LICENSE). Dataset items written for this project: CC-BY-4.0 (see [DATASETS.md](DATASETS.md)).
