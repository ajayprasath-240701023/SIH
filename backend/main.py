"""
FastAPI application entry-point.

Run with:  uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import config
from backend.routers import trace, cases

# ── App ────────────────────────────────────────────────────
app = FastAPI(
    title="Crypto Fraud Attribution System",
    description="Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges",
    version="1.0.0",
)

# ── CORS ───────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────
app.include_router(trace.router)
app.include_router(cases.router)

# ── Serve frontend static files ───────────────────────────
app.mount("/", StaticFiles(directory=str(config.FRONTEND_DIR), html=True), name="frontend")


# ── Health check ──────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "mode": config.MODE}
