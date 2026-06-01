FROM python:3.12-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --compile-bytecode

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend/src
ENV RAYA_TRADE_ENVIRONMENT=docker

COPY backend ./backend/

WORKDIR /app/backend

EXPOSE 8080

# Migrations run in __main__ before the app starts; override with RAYA_SKIP_MIGRATIONS=true
CMD ["python", "-m", "raya_faraz_agent"]
