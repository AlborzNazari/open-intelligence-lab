"""
api/main.py  —  v7.2.0
CORS + auth + router registration for Open Intelligence Lab API.

On startup, initialises the auth database, then reads MISP_URL and MISP_KEY
from environment variables. If both are set, the MISP live feed scheduler
starts automatically and begins pulling threat intelligence in the background.
If not set, the app runs normally on static curated datasets.

Authentication: /auth/* provides register, login, and account management.
Every /intelligence/* endpoint requires a valid JWT carrying a known role
(analyst or admin), enforced at the router level.
"""

import os
import sys
import shutil
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.intelligence.router import router as intelligence_router
from backend.auth import init_db, require_role
from backend.auth_router import router as auth_router

logger = logging.getLogger(__name__)

API_VERSION = "7.2.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("[Startup] Auth database initialised")

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

    yield

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
    version=API_VERSION,
    lifespan=lifespan,
    description=(
        "Ethical OSINT research platform — graph-based threat modeling, "
        "explainable risk analytics, STIX 2.1 export, TAXII 2.1 feed ingestion, "
        "MISP integration, and provenance-validated live intelligence.\n\n"
        "**Authentication:** register and log in at `/auth`. Every "
        "`/intelligence/*` endpoint requires a Bearer token with an analyst "
        "or admin role.\n\n"
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

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/auth", tags=["auth"])

app.include_router(
    intelligence_router,
    dependencies=[Depends(require_role("analyst", "admin"))],
)


# ─── Root & Health ────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    misp_active = bool(os.getenv("MISP_URL") and os.getenv("MISP_KEY"))
    return {
        "status": "ok",
        "version": API_VERSION,
        "docs": "/docs",
        "misp_live_feed": (
            "active - pulling from " + os.getenv("MISP_URL", "")
            if misp_active
            else "inactive - set MISP_URL and MISP_KEY to activate"
        ),
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": API_VERSION}


# ─── Static UI ────────────────────────────────────────────────────────────────
# Serve only index.html and auth.html from a safe subdirectory.
# The previous mount used ".." (repo root), which exposed fly.toml,
# Dockerfile, backend/, requirements.txt and everything else at /ui/*.
try:
    _root = os.path.join(os.path.dirname(__file__), "..")
    _safe_dir = os.path.join(_root, "visualization")
    os.makedirs(_safe_dir, exist_ok=True)
    for _f in ["index.html", "auth.html"]:
        _src = os.path.join(_root, _f)
        _dst = os.path.join(_safe_dir, _f)
        if os.path.exists(_src) and not os.path.exists(_dst):
            shutil.copy2(_src, _dst)
    app.mount(
        "/ui",
        StaticFiles(directory=_safe_dir, html=True),
        name="static",
    )
except Exception:
    pass
