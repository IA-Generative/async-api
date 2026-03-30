#!/bin/bash
set -e

API_PORT="${PORT:-8000}"
API_HOST="${HOST:-0.0.0.0}"
APP="${APP:-api}"

run_migrations() {
    echo "Verifying and running Alembic migrations..."
    if [ ! -f "alembic.ini" ]; then
        echo "❌ alembic.ini file not found"
        exit 1
    fi

    if [ ! -d "migrations" ]; then
        echo "❌ migrations directory not found"
        exit 1
    fi

    echo "⬆️  Applying migrations..."
    if ! alembic upgrade head; then
        echo "❌ Failed to apply migrations"
        exit 1
    fi

    echo "✅ Migrations applied successfully!"
}

start_api_dev() {
    uvicorn --host "$API_HOST" \
        --port "$API_PORT" api.main:app \
        --reload
}
start_listener_dev() {
    nodemon --legacy-watch --exec python3 listener/main.py
}

main() {
    echo "Mode: $APP (development)"
    echo "📦 Syncing dependencies..."
    uv sync

    case "${APP,,}" in
        "api")
            echo "Running migrations before starting API..."
            run_migrations
            start_api_dev
            ;;
        "listener")
            echo "Starting listener mode..."
            start_listener_dev
            ;;
        *)
            echo "❌ Unrecognized application mode: $APP"
            echo "   Available modes: api, listener"
            exit 1
            ;;
    esac
}

trap 'echo "🛑 Stopping development service..."; exit 0' SIGTERM SIGINT
main "$@"