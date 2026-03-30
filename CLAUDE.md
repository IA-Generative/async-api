# CLAUDE.md

## Project overview

AsyncTaskAPI — A Python async task management API for dispatching and tracking distributed tasks across services via RabbitMQ.

**Stack:** Python 3.13+, FastAPI, SQLAlchemy + AsyncPG, PostgreSQL 17, RabbitMQ (aio-pika), Alembic, Docker/K8s (Helm)

## Architecture

```
Client → API (creates task in DB + publishes to RabbitMQ) → Worker (processes) → Listener (updates DB + sends callback)
```

Three main components:
- **API** (`api/`) — FastAPI REST service for task submission and polling
- **Listener** (`listener/`) — Consumes worker results from RabbitMQ, updates DB, sends callbacks (HTTP/AMQP)
- **Workers** (`workers/`) — Task executors in Python, JS, or TS

### Layers (API)

Routes (`api/routes/`) → Services (`api/services/`) → Repositories (`api/repositories/`) → Models (`api/models/`)

Schemas (Pydantic) live in `api/schemas/`.

## Key endpoints

- `POST /v1/services/{service}/tasks` — Submit a task
- `GET /v1/services/{service}/tasks/{task_id}` — Poll task status
- `GET /v1/services` — List available services
- `/internal/health`, `/internal/ready`, `/internal/metrics`

## Key files

- `api/main.py` — FastAPI app entrypoint
- `api/core/config.py` — Settings (env-based)
- `api/core/database.py` — Async SQLAlchemy engine setup
- `api/models/task.py` — Task ORM model (SQLModel)
- `config/services.yaml` — Service definitions (queues, schemas, quotas)
- `config/clients.yaml` — Client auth and quotas
- `listener/main.py` — Listener entrypoint
- `Makefile` — 30+ dev commands
- `docker-compose.yml` — Full dev environment (api, listener, consumer, db, broker)

## Configuration

- Services defined in `config/services.yaml` (input/output queues, JSON schema validation, quotas)
- Clients defined in `config/clients.yaml` (client_id, per-service authorizations, quotas)
- Environment variables in `.env` (see `.env.example`)

## Database

- PostgreSQL 17 via AsyncPG
- Alembic migrations in `migrations/versions/`
- Main model: `Task` (task_id, client_id, service, status, request, response, progress, callback, dates, worker_host)

## Commands

- `make install` — Install deps via uv
- `make up` / `make down` — Docker Compose stack
- `make lint` — `uv run ruff check .`
- `make format` — `uv run ruff format .`
- `make test` — `uv run pytest -v -s --cov=api --cov=listener --cov=src --cov-report=term-missing --disable-warnings`
- `make migration-upgrade` — Apply DB migrations
- `make logs-api` / `make logs-listener` — View service logs

## Before committing

- Run linting: `uv run ruff check .`
- Run tests: `uv run pytest -v -s --cov=api --cov=listener --cov=src --cov-report=term-missing --disable-warnings`
