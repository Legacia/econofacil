"""Rotas administrativas (/admin): agendador de expirações (RN-021)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import scheduler
from app.core.database import get_db
from app.core.deps import CurrentUser, require_role
from app.models.user import UserRole
from app.services import expiration_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/admin", tags=["admin"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
Admin = Annotated[object, Depends(require_role(UserRole.ADMIN))]


@router.post("/expirations/run")
async def run_expirations_now(db: DbSession, user: CurrentUser, _: Admin):
    """Dispara a rotina de expirações agora e devolve o que foi processado."""
    result = await expiration_service.run_expirations(db)
    await log_action(db, action="admin.expirations_run", user_id=user.id, details=result)
    return result


@router.get("/scheduler")
async def scheduler_status(_: Admin):
    return dict(scheduler.state)
