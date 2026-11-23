# Contributing to touchstone

Thank you for helping! Please read the [Code of Conduct](CODE_OF_CONDUCT.md) first.

## Ways to help

| You are good at | You can |
|---|---|
| Hindi or Hinglish (no coding) | Review questions in a spreadsheet: open a [reviewer issue](https://github.com/harshita2012sharma-max/Touchstone/issues/new?template=become_a_reviewer.yml). This is the most valuable help right now. |
| Writing | Write new questions (see below), improve the README, or translate docs into Hindi. |
| Python | Fix a bug, add a provider, add a task, improve scoring. |
| React / CSS | Improve the web UI (`ui/`). |
| Spreading the word | Try touchstone on a model and share what you found, with the settings and sample size. |

## Good first issues

Look for issues labelled [`good first issue`](https://github.com/harshita2012sharma-max/Touchstone/labels/good%20first%20issue). Ideas that are always welcome:

- Add 10 original questions to one task (for example Hinglish sarcasm or Hindi idioms).
- Review 20 pending questions with the review sheet.
- Translate the Quickstart section of the README into Hindi.
- Add a missing example to a task's `<details>` block in the README.
- Improve an error message that confused you.
- Add a test for an edge case in `scoring/` (for example Devanagari digits or Indian number grouping).

Comment on an issue before starting so two people do not do the same work.

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

Each item needs **at least two reviewers other than its author**, who are fluent in Hindi or Hinglish. Items with fewer reviewers stay in `datasets/pending/` and are not scored.

### Reviewer checklist

- [ ] Factually correct, with exactly one correct answer
- [ ] Natural Hindi or Hinglish, as people really write it
- [ ] Neutral: no religion comparisons, caste, politics, "which group is better" questions, or regional stereotypes
- [ ] No sexual, hateful or offensive content
- [ ] Not copied from any existing source

## Adding a new task

1. Add a task class in `src/touchstone_llm/tasks/` (multiple choice: subclass `MCQTask`; translation-style: subclass `TranslationHiEn` with a new `prompt_template`).
2. Register it in `src/touchstone_llm/tasks/__init__.py`.
3. Add at least 20 original draft items to `datasets/pending/<task>.jsonl` and run `python -m touchstone_llm.review check`.
4. Add a friendly name in `ui/src/lib.ts` and `src/touchstone_llm/leaderboard.py`, and an example in the README.
5. Run the full checks and open a pull request.

Third-party packages can also add tasks without changing touchstone, through the `touchstone_llm.tasks` entry point.

## Recognition

Every merged contribution and every reviewer is credited in the [README](README.md#contributors) and in the release notes.

## Wording rules

Use neutral language in code, docs and results. Never claim a model is "best" or "most accurate"; report numbers with their settings and sample size.

## Pull requests

- Keep each PR small and focused.
- Add or update tests.
- Add a line to `CHANGELOG.md` under "Unreleased".
- Never commit API keys or `.env` files.
