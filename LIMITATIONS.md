# Limitations

Please read this before using any kasauti result.

- **Small dataset.** v1 has about 25 items per task. Small differences between models are often noise.
- **Hindi is not all of India.** India has many languages and dialects. Good results here say nothing about other Indian languages or about every variety of Hindi.
- **Code-mixed text varies.** Hinglish has no standard spelling, so rule-based scoring can miss valid answers.
- **Translation scores are rough.** chrF compares against one or two reference translations and can penalise correct paraphrases.
- **API models change.** Providers can update a model behind the same name. Every result records the test date and model id, but older results may not be repeatable.
- **Answer format affects scores.** If a model's answer cannot be parsed, the item counts as wrong. Reports show this "unparsed" rate separately.
