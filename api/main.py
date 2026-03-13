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


MIT License

Copyright (c) 2026 Alborz Nazari

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
