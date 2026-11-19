# Contributing to touchstone

Thank you for helping! Please read the [Code of Conduct](CODE_OF_CONDUCT.md) first.

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy && pytest
```

Tests never call real APIs. Use the mock backend.

## Adding dataset items

Every item must be **written by you**. Do not copy from exams, books, websites or other datasets. By submitting an item you agree to license it under CC-BY-4.0.

Each item needs **at least two reviewers other than its author**, who are fluent in Hindi or Hinglish. Items with fewer reviewers stay in `data/pending/` and are not scored.

### Reviewer checklist

- [ ] Factually correct, with exactly one correct answer
- [ ] Natural Hindi or Hinglish, as people really write it
- [ ] Neutral: no religion comparisons, caste, politics, "which group is better" questions, or regional stereotypes
- [ ] No sexual, hateful or offensive content
- [ ] Not copied from any existing source

## Wording rules

Use neutral language in code, docs and results. Never claim a model is "best" or "most accurate"; report numbers with their settings and sample size.

## Pull requests

- Keep each PR small and focused.
- Add or update tests.
- Add a line to `CHANGELOG.md` under "Unreleased".
- Never commit API keys or `.env` files.
