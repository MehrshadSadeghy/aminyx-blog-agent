# Standard build — official Docker Hub + PyPI (no mirrors).
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend/src \
    RAYA_TRADE_ENVIRONMENT=docker

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

WORKDIR /app/backend

RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 8085

ENV UVICORN_WORKERS=7

CMD ["/app/backend/entrypoint.sh"]
