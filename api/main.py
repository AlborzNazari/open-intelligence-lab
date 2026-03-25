"""
api/main.py  —  v0.4.0
CORS + router registration for Open Intelligence Lab API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.intelligence.router import router as intelligence_router

app = FastAPI(
    title="Open Intelligence Lab API",
    version="0.4.0",
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
# Three scenarios that need CORS access:
#
#   1. Local dev  — index.html opened from file:// or a local dev server
#   2. GitHub Pages — https://alborznazari.github.io fetching localhost API
#      NOTE: browsers block https→http (mixed-content) by default.
#      Users must either:
#        a) run the API behind a local HTTPS proxy (see README), OR
#        b) open the GitHub Pages URL in Firefox and set
#           security.mixed_content.block_active_content = false in about:config
#        c) use the local index.html (file://) which talks to http:// fine
#   3. Any localhost port (e.g. Vite dev server on :5173)
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # ── Local file:// and localhost origins ───────────────────────────
        "null",                          # file:// pages send Origin: null
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost:5173",         # Vite
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # ── GitHub Pages (static dashboard) ──────────────────────────────
        # Requests from GitHub Pages arrive as https:// origins.
        # The browser will still enforce mixed-content rules on the CLIENT
        # side (blocking https page → http API). This CORS entry ensures
        # that IF the browser allows the request (e.g. Firefox with mixed-
        # content unlocked, or API served over HTTPS), the server won't
        # additionally reject it with a CORS 403.
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
    return {
        "status": "ok",
        "version": "0.4.0",
        "docs": "/docs",
        "note": (
            "If calling from GitHub Pages (https), the browser enforces "
            "mixed-content rules. Run the API over HTTPS or use the local "
            "index.html to connect without restrictions."
        ),
    }
