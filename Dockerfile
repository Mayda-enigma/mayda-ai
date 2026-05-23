# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base

# System deps for whisper (ffmpeg) and scientific Python wheels (gcc not strictly
# needed since wheels are precompiled, but harmless on slim).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

# uv: fast, deterministic installs from the lockfile.
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies (cached layer — only rebuilds when lockfile changes).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application source.
COPY src ./src

# Install the project itself.
RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1 \
    PORT=8101 \
    HF_HOME=/cache/hf \
    INVENTORY_DATABASE_URL="sqlite:////data/inventory.db" \
    INVENTORY_MODEL_PATH="/data/models.joblib" \
    CHROMA_DB_DIR="/chroma"

EXPOSE 8101

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/api/health || exit 1

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8101"]
