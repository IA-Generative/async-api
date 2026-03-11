FROM python:3.14-slim AS base

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest uv /usr/local/bin/uv

# Install dependencies
COPY --chown=appuser:appuser pyproject.toml .
RUN uv sync

# Copying the application code
COPY --chown=appuser:appuser api api
COPY --chown=appuser:appuser listener listener
COPY --chown=appuser:appuser migrations migrations
COPY --chown=appuser:appuser alembic.ini .

ENV PATH=/app/.venv/bin/:$PATH
ENV PYTHONPATH=/app

RUN groupadd -g 1001 appuser && useradd -u 1001 -g 1001 -m -s /bin/bash appuser \
    && chown -R appuser:appuser /app

CMD ["./entrypoint.sh"]

FROM base AS dev

COPY --chown=appuser:appuser scripts/entrypoint_dev.sh /app/entrypoint.sh

RUN apt-get update -y && apt-get install -y npm
RUN npm install -g nodemon

USER appuser

FROM base AS prod

COPY --chown=appuser:appuser scripts/entrypoint.sh /app/entrypoint.sh

USER appuser