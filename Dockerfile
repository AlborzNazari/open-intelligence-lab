# ─────────────────────────────────────────────────────────────────────────────
# Open Intelligence Lab — Dockerfile
# v0.4.0
#
# Built a self-contained container for the OI Lab FastAPI backend.
# MISP is NOT bundled here on previous v0.3.0 use docker-compose.yml to spin up both
# OI Lab + a MISP instance together (recommended for development).
#
# Standalone usage (no MISP):
#   docker build -t open-intelligence-lab .
#   docker run -p 8000:8000 open-intelligence-lab
#
# With MISP (recommended):
#   docker compose up
#
# Author: Alborz Nazari
# License: MIT
# Note end
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# ── System deps ───────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy requirements first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project files ────────────────────────────────────────────────────────
COPY api/         ./api/
COPY backend/     ./backend/
COPY core_engine/ ./core_engine/
COPY datasets/    ./datasets/
COPY visualization/ ./visualization/

# ── Environment defaults (override at runtime via -e or docker-compose) ───────
# Leave MISP_URL and MISP_KEY unset by default — app runs on static data
ENV PYTHONPATH=/app
ENV MISP_URL=""
ENV MISP_KEY=""
ENV MISP_LABEL="MISP-Live"
ENV MISP_PULL_DAYS="7"
ENV MISP_LIMIT="200"
ENV MISP_VERIFY_SSL="true"
ENV MISP_INTERVAL_SECONDS="3600"

# ── Expose API port ───────────────────────────────────────────────────────────
EXPOSE 8000

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# ── Start server ──────────────────────────────────────────────────────────────
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
