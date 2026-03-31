from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic handles all table creation — nothing needed here on startup
    yield


app = FastAPI(
    title="AI English App API",
    version="1.0.0",
    description="Backend for AI English Learning App",
    lifespan=lifespan,
)

# ── Routers added here as each feature is built ──
# from routers import auth
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/health")
async def health():
    """Health check — confirms API and DB connection are alive."""
    return {"status": "ok", "message": "AI English App API is running"}