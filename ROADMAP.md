# Roadmap

Where touchstone is going. Ideas and help are welcome on any item; open an issue to discuss.

## Now

- **Human review of the 350 draft questions.** Two reviewers per item, other than the author. This unlocks official results. [Volunteer](https://github.com/harshita2012sharma-max/Touchstone/issues/new?template=become_a_reviewer.yml).
- **More hard questions** for the newer tasks (grammar, idioms, logic, English to Hindi, Hinglish to Hindi), tested against several models before they ship.

## Next

- **First public results** for popular models, with dates, model ids, settings and sample sizes, made with `touchstone leaderboard`.
- **Publish the reviewed questions as a Hugging Face dataset** with a dataset card.
- **Contribute the reviewed tasks upstream** to widely used evaluation tools (EleutherAI lm-evaluation-harness, Hugging Face LightEval), so more people can run them.

## Later

- More Indian languages and scripts (for example Marathi, Bengali, Tamil), each with native-speaker reviewers.
- Spoken-style Hinglish (voice-assistant transcripts) and longer reading passages.
- A results page that updates when new models are released.

## Not planned

- An AI judge for scoring. touchstone keeps fixed, checkable rules so results can be reproduced.
- Naming a single "best" model. Results are reported as numbers with their sample sizes.
