FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update &&\
    apt-get install -y gcc &&\
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1001 appuser && useradd -u 1001 -g 1001 -m -s /bin/bash appuser \
    && chown -R appuser:appuser /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --chown=appuser:appuser    pyproject.toml  uv.lock ./

RUN uv sync
COPY main.py ./
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8083
CMD ["python", "main.py"]
