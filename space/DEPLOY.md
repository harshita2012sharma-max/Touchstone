# Deploying the online demo

The two files next to this one (`Dockerfile`, `README.md`) are the whole Space.

1. Release touchstone-llm 0.3.0 or newer to PyPI (the Dockerfile installs it from there).
2. Create a Space at https://huggingface.co/new-space: SDK **Docker**, template **Blank**, hardware **CPU basic** (free).
3. Upload `Dockerfile` and `README.md` from this folder to the Space (web upload or `git push`).
4. Wait for the build, then open the Space. Only "Practice (mock)" is offered and key saving is refused.

Do not add API keys as Space secrets: demo mode ignores real providers on purpose.
