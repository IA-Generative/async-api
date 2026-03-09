FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest uv /usr/local/bin/uv

# Install necessary packages
RUN apt-get update -y \
    && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1001 appuser && useradd -u 1001 -g 1001 -m -s /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Install dependencies
COPY --chown=appuser:appuser pyproject.toml .
RUN uv sync

# Copying the application code
COPY --chown=appuser:appuser api api
COPY --chown=appuser:appuser listener listener
COPY --chown=appuser:appuser migrations migrations
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser scripts/entrypoint.sh /app/entrypoint.sh

ENV PATH=/app/.venv/bin/:$PATH
ENV PYTHONPATH=/app

CMD ["./entrypoint.sh"]