# ─────────────────────────────────────────────────────────────────────────────
# Open Intelligence Lab — Dockerfile v0.6.0
#
# Standalone usage (no MISP):
#   docker build -t open-intelligence-lab .
#   docker run -p 8000:8000 open-intelligence-lab
#
# With MISP (recommended for full stack):
#   docker compose up
#
# Build args (set automatically by GitLab CI):
#   VERSION   — semantic version string (e.g. v0.6.0)
#   GIT_SHA   — full commit SHA for traceability
#
# Author: Alborz Nazari — https://github.com/AlborzNazari/open-intelligence-lab
# License: MIT
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# ── Build args (passed in by CI; safe to leave unset for local builds) ────────
ARG VERSION=dev
ARG GIT_SHA=unknown

# ── OCI image labels for registry traceability ────────────────────────────────
LABEL org.opencontainers.image.title="Open Intelligence Lab"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${GIT_SHA}"
LABEL org.opencontainers.image.source="https://github.com/AlborzNazari/open-intelligence-lab"
LABEL org.opencontainers.image.licenses="MIT"

# ── System deps ───────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy requirements first — Docker layer cache skips pip on unchanged deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project source ───────────────────────────────────────────────────────
COPY api/         ./api/
COPY backend/     ./backend/
COPY core_engine/ ./core_engine/
COPY datasets/    ./datasets/
COPY visualization/ ./visualization/

# ── Runtime environment defaults ─────────────────────────────────────────────
# MISP_URL / MISP_KEY unset → app runs on static curated datasets
# Override at runtime via: docker run -e MISP_URL=... -e MISP_KEY=...
ENV PYTHONPATH=/app
ENV VERSION=${VERSION}
ENV GIT_SHA=${GIT_SHA}
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
# /health is faster than / — no MISP status check logic
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Non-root user for security ────────────────────────────────────────────────
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# ── Start server ──────────────────────────────────────────────────────────────
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
