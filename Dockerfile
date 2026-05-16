FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md ./
COPY src ./src
COPY examples ./examples
COPY docs ./docs

RUN python -m pip install --upgrade pip && \
    python -m pip install .

USER app

ENTRYPOINT ["python", "-m", "gossipsub_large_msg_lab"]
CMD ["--help"]
