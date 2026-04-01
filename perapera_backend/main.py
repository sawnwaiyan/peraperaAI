from fastapi import FastAPI
from contextlib import asynccontextmanager

from routers import auth
# from routers import users        # Week 4
# from routers import missions     # Week 2
# from routers import results      # Week 2
# from routers import voice        # Week 3
# from routers import openai_proxy # Week 4


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Table creation is handled by Alembic — no create_all here.
    yield


app = FastAPI(
    title="PeraperaAI — Backend API",
    version="1.0.0",
    description="AI English learning app for Japanese users.",
    lifespan=lifespan,
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}