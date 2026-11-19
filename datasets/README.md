# Dataset review guide

New items wait in `datasets/pending/` until **two people other than the author** approve them. Pending items are never scored.

## For reviewers (no coding needed)

You will get a spreadsheet (`.csv`). Open it in Excel or Google Sheets. For each row:

1. Read the `prompt` exactly as the model will see it, and the `expected` answer.
2. Write one word in `verdict`:
   - `ok`: correct and good to use
   - `fix`: small problem; explain it in `comment`
   - `reject`: should not be used; explain why in `comment`
3. Save as CSV (UTF-8) and send it back.

Please check:

- [ ] The expected answer is correct, and it is the **only** correct answer.
- [ ] The Hindi or Hinglish sounds natural, the way people really write.
- [ ] It is neutral: no religion comparisons, caste, politics, "which group is better", or regional stereotypes.
- [ ] Nothing sexual, hateful or offensive.
- [ ] It does not look copied from a textbook, exam or website.

If you are unsure about a fact, mark `fix` and say so. That is better than guessing.

## For maintainers

```bash
python -m kasauti.review check                                  # validate pending items
python -m kasauti.review export review.csv                       # sheet for reviewers
python -m kasauti.review import review_asha.csv --reviewer asha  # record one reviewer's verdicts
python -m kasauti.review promote                                 # ship items with 2+ approvals
```

After `promote`, run `pytest` and open a pull request. Reviewers are credited in the README.
