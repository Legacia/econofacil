"""Endpoints da Noor (/noor) — visão do motor de otimização (Noor Monitor)."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.noor import solver as noor_solver
from app.schemas.recommendation import RecommendationItem
from app.services import noor_reco_service, optimizer_service

router = APIRouter(prefix="/noor", tags=["noor"])
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/status")
async def noor_status():
    available = noor_solver.solver_available()
    if settings.NOOR_FORCE_HEURISTIC:
        engine = "heuristic"
    elif settings.NOOR_SOLVER_ENABLED and available:
        engine = "noor-ilp"
    else:
        engine = "heuristic"
    return {
        "version": noor_solver.NOOR_SOLVER_VERSION,
        "engine": engine,
        "solver_available": available,
        "solver_enabled": settings.NOOR_SOLVER_ENABLED,
        "min_split_savings": optimizer_service.MIN_SPLIT_SAVINGS,
        "max_stores": optimizer_service.MAX_STORES,
        "metrics": optimizer_service.get_metrics(),
        "recommendations": {"version": noor_reco_service.RECO_VERSION, "methods": ["also-bought", "usual"]},
    }


# --------------------------------------------------------------------------- #
# Noor V2 — recomendações contextuais (RN-023)
# --------------------------------------------------------------------------- #
@router.get("/recommendations/also-bought", response_model=list[RecommendationItem])
async def also_bought(
    product_id: uuid.UUID, db: DbSession, limit: Annotated[int, Query(ge=1, le=20)] = 5
):
    """Quem comprou este produto também comprou (agregado, sem dados pessoais)."""
    return await noor_reco_service.also_bought(db, product_id, limit)


@router.get("/recommendations/usual", response_model=list[RecommendationItem])
async def usual_purchases(
    db: DbSession, user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=20)] = 6,
    min_orders: Annotated[int, Query(ge=2, le=20)] = 2,
):
    """Você costuma comprar: itens recorrentes que não estão no carrinho agora."""
    return await noor_reco_service.usual(db, user, limit, min_orders)
