"""Ponto de entrada da aplicação EconoFácil API."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Em desenvolvimento, cria as tabelas automaticamente.
    # Em produção, use migrações Alembic (alembic upgrade head).
    if not settings.is_production:
        from app.core.database import engine
        from app.models import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    # RN-021: agendador de expirações (desligado nos testes)
    from app.core import scheduler

    if settings.SCHEDULER_ENABLED and settings.ENVIRONMENT != "test":
        scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Backend do ecossistema de compras inteligentes EconoFácil.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
# Modo demonstração local: sem limite de tentativas (o usuário alterna entre contas de teste)
if settings.LOCAL_DEMO:
    limiter.enabled = False
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["infra"])
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT, "demo": settings.LOCAL_DEMO}


# ---------------------------------------------------------------------------
# Servir o front-end (build do React) na mesma origem, quando STATIC_DIR existe.
# Em dev/local/testes a variável não é definida e nada disto roda.
# ---------------------------------------------------------------------------
import os  # noqa: E402
from pathlib import Path  # noqa: E402

_static_dir = os.getenv("STATIC_DIR")
if _static_dir and Path(_static_dir).is_dir():
    from fastapi.responses import FileResponse  # noqa: E402
    from fastapi.staticfiles import StaticFiles  # noqa: E402

    _static = Path(_static_dir)
    _index = _static / "index.html"
    if (_static / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=_static / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # rotas de API/infra não caem aqui; o resto serve o index (SPA)
        if full_path.startswith(("api", "docs", "redoc", "openapi", "health")):
            from fastapi import HTTPException

            raise HTTPException(status_code=404)
        candidate = _static / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_index)

