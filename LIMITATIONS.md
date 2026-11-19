# Limitations

Please read this before using any touchstone result.

- **Small dataset.** v1 has about 25 items per task. Small differences between models are often noise.
- **Hindi is not all of India.** India has many languages and dialects. Good results here say nothing about other Indian languages or about every variety of Hindi.
- **Code-mixed text varies.** Hinglish has no standard spelling, so rule-based scoring can miss valid answers.
- **Translation scores are rough.** chrF compares against one or two reference translations and can penalise correct paraphrases.
- **API models change.** Providers can update a model behind the same name. Every result records the test date and model id, but older results may not be repeatable.
- **Answer format affects scores.** If a model's answer cannot be parsed, the item counts as wrong. Reports show this "unparsed" rate separately.
- **Numeric answers.** touchstone takes the first number after the last "Answer"/"उत्तर" marker, or else the last number in the reply. A model that reasons correctly but writes another number last can be scored wrong.
- **Instruction following is strict.** An answer scores 1 only if every rule check passes; partial success scores 0 (the report shows which checks failed).
- **Seeds are best effort.** touchstone always sends temperature 0 and seed 42, but some providers ignore the seed, so repeated runs can still differ slightly.
- **English instructions.** v1 prompt templates give format instructions in English (the content is in Hindi or Hinglish). Models that struggle with English instructions may be under-scored.
