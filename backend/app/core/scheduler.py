"""Agendador de expirações em segundo plano (RN-021).

Um único laço ``asyncio`` por processo. LIMITAÇÃO CONHECIDA: com vários workers/réplicas
cada processo teria o seu laço (a rotina é idempotente, então é seguro, mas redundante);
em produção multi-worker use um único worker agendador, um cron ou uma fila.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger("econofacil.scheduler")

state: dict = {"running": False, "interval": None, "last_run_at": None, "last_result": None, "runs": 0}
_task: asyncio.Task | None = None


async def run_once() -> dict:
    from app.core.database import AsyncSessionLocal
    from app.services import expiration_service

    async with AsyncSessionLocal() as db:
        result = await expiration_service.run_expirations(db)
    state["last_run_at"] = datetime.now(timezone.utc).isoformat()
    state["last_result"] = result
    state["runs"] += 1
    return result


async def _loop(interval: int) -> None:
    while True:
        try:
            await run_once()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — o laço nunca pode morrer
            logger.exception("Falha na rotina de expirações")
        await asyncio.sleep(interval)


def start() -> None:
    global _task
    if _task is not None and not _task.done():
        return
    interval = max(5, settings.SCHEDULER_INTERVAL_SECONDS)
    state.update(running=True, interval=interval)
    _task = asyncio.create_task(_loop(interval))


async def stop() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
        _task = None
    state["running"] = False
