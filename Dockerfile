# syntax=docker/dockerfile:1.7
#
# Single-stage build — avoids cross-stage COPY of the 1.3 GB .venv.
# uv sync + cleanup in one RUN so the full untrimmed venv never lands
# in a permanent layer.

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

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY alembic ./alembic

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    uv cache prune && \
    pip uninstall -y uv 2>/dev/null; \
    find /app/.venv -name '*.pyc' -delete && \
    find /app/.venv -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8101

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/api/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8101"]
