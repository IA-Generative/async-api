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
        echo "   Check the logs above for more details"
        exit 1
    fi

    echo "✅ Migrations applied successfully!"
}

start_api() {
    exec uvicorn --host "$API_HOST" \
        --port "$API_PORT" api.main:app \
        --workers ${API_WORKERS:-1}
}

wait_for_database() {
    local host port
    host=$(echo "${DATABASE_URL}" | sed -E 's|.*@([^:/]+):([0-9]+)/.*|\1|')
    port=$(echo "${DATABASE_URL}" | sed -E 's|.*@([^:/]+):([0-9]+)/.*|\2|')

    echo "⏳ Waiting for database at $host:$port..."
    until (echo > /dev/tcp/"$host"/"$port") 2>/dev/null; do
        echo "   Database not ready, retrying in 2s..."
        sleep 2
    done
    echo "✅ Database is ready!"
}

start_listener() {
    wait_for_database
    exec python3 listener/main.py
}

main() {
    echo "Mode: $APP"

    case "${APP,,}" in
        "api")
            echo "Running migrations before starting API..."
            run_migrations
            start_api
            ;;
        "listener")
            echo "Starting listener mode..."
            start_listener
            ;;
        *)
            echo "❌ Unrecognized application mode: $APP"
            echo "   Available modes: api, listener"
            exit 1
            ;;
    esac
}

trap 'echo "🛑 Stopping service..."; exit 0' SIGTERM SIGINT
main "$@"
