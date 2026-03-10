"""
api/main.py  —  v0.2.0
Adds CORS so the dashboard (any localhost port or file://) can call the API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.intelligence.router import router as intelligence_router

app = FastAPI(
    title="Open Intelligence Lab API",
    version="0.2.0",
    description=(
        "Ethical OSINT research platform — graph-based threat modeling "
        "and explainable risk analytics."
    ),
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allows the dashboard (opened via file:// or any localhost port) to fetch
# from this API without browser CORS errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "null",          # file:// origin that browsers send for local HTML files
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
    return {"status": "ok", "version": "0.2.0", "docs": "/docs"}
