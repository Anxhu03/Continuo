#!/bin/sh
set -e

echo "=== Starting Continuo Backend Service ==="

# Execute database migrations safely in a single process before worker initialization
echo "Applying database migrations (Alembic)..."
alembic upgrade head
echo "Database migrations applied successfully."

# Start Uvicorn ASGI Server
PORT="${PORT:-8008}"
WORKERS="${UVICORN_WORKERS:-2}"

echo "Starting Uvicorn server on port ${PORT} with ${WORKERS} workers..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
