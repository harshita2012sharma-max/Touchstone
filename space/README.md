---
title: touchstone
emoji: 🪨
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
short_description: Small, reproducible LLM tests in Hindi and Hinglish
---

# touchstone online demo

Try the [touchstone](https://github.com/harshita2012sharma-max/Touchstone) web UI
in your browser. This demo runs the **practice model** only, which needs no key:
pick topics, start a test, and open the report.

To test real models (Gemini, Groq, OpenRouter, OpenAI, Claude, Ollama and more)
with your own key, install it on your computer:

```bash
python -m pip install "touchstone-llm[ui]"
python -m touchstone_llm ui
```

or open the [Colab notebook](https://colab.research.google.com/github/harshita2012sharma-max/Touchstone/blob/main/notebooks/touchstone_colab.ipynb).
Saving API keys is switched off here on purpose: a public demo is a shared
machine, and your key should never be stored on one.
