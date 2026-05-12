"""
api/main.py  —  v0.7.0
CORS + router registration for Open Intelligence Lab API.
 
On startup, reads MISP_URL and MISP_KEY from environment variables.
If both are set, the MISP live feed scheduler starts automatically
and begins pulling threat intelligence in the background.
If not set, the app runs normally on static curated datasets.
"""
 
import os
import sys
import logging
from contextlib import asynccontextmanager
 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
 
from api.intelligence.router import router as intelligence_router
from backend.auth import init_db
from backend.auth_router import router as auth_router
 
logger = logging.getLogger(__name__)
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── On startup: wire up MISP if env vars are set ──────────────────────────
    misp_url = os.getenv("MISP_URL", "").strip()
    misp_key = os.getenv("MISP_KEY", "").strip()
 
    if misp_url and misp_key:
        try:
            backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
 
            from feed_scheduler import get_scheduler, MISPFeedConfig
 
            scheduler = get_scheduler()
            scheduler.add_misp_feed(
                MISPFeedConfig(
                    label=os.getenv("MISP_LABEL", "MISP-Live"),
                    base_url=misp_url,
                    api_key=misp_key,
                    pull_days=int(os.getenv("MISP_PULL_DAYS", "7")),
                    limit=int(os.getenv("MISP_LIMIT", "200")),
                    verify_ssl=os.getenv("MISP_VERIFY_SSL", "true").lower() == "true",
                )
            )
 
            interval = int(os.getenv("MISP_INTERVAL_SECONDS", "3600"))
            scheduler.start_background(interval_seconds=interval)
            logger.info(
                f"[Startup] MISP live feed active — {misp_url} "
                f"— pulling every {interval}s"
            )
        except Exception as e:
            logger.error(f"[Startup] MISP feed failed to start: {e}")
    else:
        logger.info(
            "[Startup] MISP_URL / MISP_KEY not set — "
            "running on static datasets. Set env vars to activate live feed."
        )
 
    yield  # server runs here
 
    # ── On shutdown: stop background scheduler cleanly ────────────────────────
    try:
        backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        from feed_scheduler import get_scheduler
        get_scheduler().stop_background()
        logger.info("[Shutdown] MISP scheduler stopped")
    except Exception:
        pass
 
 
app = FastAPI(
    title="Open Intelligence Lab API",
    version="0.7.0",
    lifespan=lifespan,
    description=(
        "Ethical OSINT research platform — graph-based threat modeling, "
        "explainable risk analytics, STIX 2.1 export, TAXII 2.1 feed ingestion, "
        "MISP integration, and provenance-validated live intelligence.\n\n"
        "**v0.7.0** — User authentication and authorisation: JWT, PBKDF2, "
        "role enforcement (analyst/admin), account lockout, audit log.\n\n"
        "**v0.6.1** — UI fidelity patch: fixed vulnerability detail field mappings, "
        "added Source column, removed static provenance badge.\n\n"
        "**MISP live feed:** set `MISP_URL` and `MISP_KEY` environment variables "
        "before starting the server to activate live threat intelligence ingestion."
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
        "https://open-intelligence-lab-cyrmjw.fly.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ─── Init DB ──────────────────────────────────────────────────────────────────
init_db()
 
# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(intelligence_router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
 
# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    misp_active = bool(os.getenv("MISP_URL") and os.getenv("MISP_KEY"))
    return {
        "status": "ok",
        "version": "0.7.0",
        "docs": "/docs",
        "misp_live_feed": (
            "active - pulling from " + os.getenv("MISP_URL", "")
            if misp_active
            else "inactive - set MISP_URL and MISP_KEY to activate"
        ),
    }
 
 
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "0.7.0"}
 
# ─── Static files (serves auth.html from repo root) ───────────────────────────
app.mount(
    "/ui",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), ".."), html=True),
    name="static",
)
