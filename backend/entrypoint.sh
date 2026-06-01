#!/bin/sh
set -e

echo "Starting uvicorn with ${UVICORN_WORKERS:-7} workers..."
exec uvicorn aminyx_suggestion_agent.app:app \
    --host 0.0.0.0 \
    --port "${API_PORT:-8085}" \
    --workers "${UVICORN_WORKERS:-7}"
