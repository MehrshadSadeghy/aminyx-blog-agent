#!/bin/sh
set -e

echo "Starting uvicorn with ${UVICORN_WORKERS:-7} workers..."
exec uvicorn raya_faraz_agent.app:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers "${UVICORN_WORKERS:-7}"
