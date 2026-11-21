# Hugging Face Space (Docker SDK) for the touchstone online demo.
# Demo mode: practice model only, no API keys can be saved. See
# src/touchstone_llm/space.py.
FROM python:3.12-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    TOUCHSTONE_RUNS_DIR=/tmp/touchstone-runs

# Needs touchstone-llm 0.3.0 or newer (the first release with demo mode).
RUN pip install --no-cache-dir --user "touchstone-llm[ui]>=0.3.0"

EXPOSE 7860
CMD ["python", "-m", "touchstone_llm.space"]
