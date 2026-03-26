"""
api/main.py  —  v0.4.0
CORS + router registration for Open Intelligence Lab API.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.intelligence.router import router as intelligence_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── On startup: wire up MISP if env vars are set ──────────────────────────
    misp_url = os.getenv("MISP_URL", "").strip()
    misp_key = os.getenv("MISP_KEY", "").strip()

    if misp_url and misp_key:
        try:
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
            from feed_scheduler import get_scheduler, MISPFeedConfig

            scheduler = get_scheduler()
            scheduler.add_misp_feed(MISPFeedConfig(
                label=os.getenv("MISP_LABEL", "MISP-Live"),
                base_url=misp_url,
                api_key=misp_key,
                pull_days=int(os.getenv("MISP_PULL_DAYS", "7")),
                limit=int(os.getenv("MISP_LIMIT", "200")),
                verify_ssl=os.getenv("MISP_VERIFY_SSL", "true").lower() == "true",
            ))

            interval = int(os.getenv("MISP_INTERVAL_SECONDS", "3600"))
            scheduler.start_background(interval_seconds=interval)
            logger.info(f"[Startup] MISP live feed started — {misp_url} — interval: {interval}s")
        except Exception as e:
            logger.error(f"[Startup] MISP feed failed to start: {e}")
    else:
        logger.info("[Startup] MISP_URL/MISP_KEY not set — running on static datasets only")

    yield  # server runs here

    # ── On shutdown ────────────────────────────────────────────────────────────
    try:
        from feed_scheduler import get_scheduler
        get_scheduler().stop_background()
    except Exception:
        pass


app = FastAPI(
    title="Open Intelligence Lab API",
    version="0.4.0",
    lifespan=lifespan,
    description=(
        "Ethical OSINT research platform — graph-based threat modeling, "
        "explainable risk analytics, STIX 2.1 export, TAXII 2.1 feed ingestion, "
        "MISP integration, and provenance-validated live intelligence.\n\n"
        "**v0.4.0** adds bidirectional TAXII: MISP feed ingestion, TAXII client, "
        "provenance chain-of-custody, confidence scoring, and staleness detection."
    ),
    contact={
        "name": "Alborz Nazari",
        "url": "https://github.com/AlborzNazari/open-intelligence-lab",
    },
    license_info={"name": "MIT"},
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "null",
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://alborznazari.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(intelligence_router)


# ─── Root health check ────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    misp_active = bool(os.getenv("MISP_URL") and os.getenv("MISP_KEY"))
    return {
        "status": "ok",
        "version": "0.4.0",
        "docs": "/docs",
        "misp_live_feed": "active" if misp_active else "inactive — set MISP_URL and MISP_KEY",
    }
