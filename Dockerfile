# syntax=docker/dockerfile:1.6

# ── Builder stage: install dependencies in a virtual environment ──
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project
COPY src ./src
COPY alembic ./alembic
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ── Runner stage: minimal runtime image ──
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8101 \
    HF_HOME=/cache/hf \
    INVENTORY_DATABASE_URL="sqlite:////data/inventory.db" \
    INVENTORY_MODEL_PATH="/data/models.joblib" \
    CHROMA_DB_DIR="/chroma"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY alembic ./alembic

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8101

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/api/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8101"]
