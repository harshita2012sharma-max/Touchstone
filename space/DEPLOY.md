# Hugging Face Space

Hugging Face now needs a paid PRO plan for Docker and Gradio Spaces. Static
Spaces are free, so there are two options.

## Free: showcase page (`showcase/`)

A static landing page in the brand colours with screenshots, the six tasks, an
"Open in Colab" button (the free way to try touchstone) and install steps.
Images load from the GitHub repository, so only two files are uploaded.

1. Open https://huggingface.co/new-space.
2. Space name `touchstone`, license Apache 2.0, SDK **Static**, template **Blank**, **Public**.
3. Press **Create Space**.
4. In the Space, open **Files** → **+ Add file** → **Upload files**, add `showcase/index.html`
   and `showcase/README.md`, and press **Commit**. Replace the README Hugging Face made.
5. The page is live in a few seconds at `https://huggingface.co/spaces/<you>/touchstone`.

## Paid (PRO): live demo (`Dockerfile`, `README.md`)

Runs the real web UI in demo mode: only the practice model, and saving keys is
refused (see `src/touchstone_llm/space.py`). Needs touchstone-llm 0.3.0 or newer
on PyPI.

1. Create a Space with SDK **Docker**, template **Blank**, hardware **CPU basic**.
2. Upload `Dockerfile` and `README.md` from this folder.
3. Wait for the build. Do not add API keys as Space secrets: demo mode ignores real providers on purpose.
