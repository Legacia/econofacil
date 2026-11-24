"""Andamento do pedido por loja (RN-019).

Cada loja de um pedido tem seu próprio status (``OrderFulfillment``). O status do
pedido inteiro é DERIVADO: enquanto houver pagamento pendente fica
``awaiting_payment``; depois de tudo pago vale a loja MAIS LENTA.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import (
    FULFILLMENT_PROGRESS, FulfillmentStatus, Order, OrderFulfillment, OrderStatus,
)
from app.models.payment import Payment, PaymentStatus


class InvalidTransition(ValueError):
    pass


class NotPaidYet(ValueError):
    pass


# status de pedido correspondente a cada nível de progresso
_PROGRESS_TO_ORDER = {
    0: OrderStatus.PLACED,
    1: OrderStatus.SEPARATING,
    2: OrderStatus.ON_THE_WAY,
    3: OrderStatus.DELIVERED,
}


def derive_from_fulfillments(fulfillments: list[OrderFulfillment]) -> OrderStatus:
    """Pedido = loja mais lenta (entre as não canceladas). Todas canceladas = cancelado."""
    active = [f for f in fulfillments if f.status != FulfillmentStatus.CANCELLED]
    if not active:
        return OrderStatus.CANCELLED if fulfillments else OrderStatus.PLACED
    slowest = min(FULFILLMENT_PROGRESS[f.status] for f in active)
    return _PROGRESS_TO_ORDER[slowest]


async def payments_of(db: AsyncSession, order_id: uuid.UUID) -> list[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.order_id == order_id).order_by(Payment.store_name)
    )
    return list(result.scalars().all())


async def sync_order_status(db: AsyncSession, order: Order) -> Order:
    """Recalcula e grava o status do pedido a partir dos pagamentos e das lojas."""
    if order.status == OrderStatus.CANCELLED:
        return order
    payments = await payments_of(db, order.id)
    if payments and any(p.status != PaymentStatus.PAID for p in payments):
        order.status = OrderStatus.AWAITING_PAYMENT
    else:
        order.status = derive_from_fulfillments(list(order.fulfillments))
    await db.commit()
    await db.refresh(order)
    return order


async def store_is_paid(db: AsyncSession, order_id: uuid.UUID, store_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Payment).where(Payment.order_id == order_id, Payment.store_id == store_id)
    )
    pays = list(result.scalars().all())
    return bool(pays) and all(p.status == PaymentStatus.PAID for p in pays)


async def advance_store(
    db: AsyncSession, order: Order, store_id: uuid.UUID, new_status: FulfillmentStatus
) -> OrderFulfillment:
    """Muda o status de UMA loja. Só avança (ou cancela) e só depois que a loja foi paga."""
    f = next((x for x in order.fulfillments if x.store_id == store_id), None)
    if f is None:
        raise LookupError("Loja não participa do pedido")
    if order.status == OrderStatus.CANCELLED or f.status in (
        FulfillmentStatus.CANCELLED, FulfillmentStatus.DELIVERED
    ):
        raise InvalidTransition("Esta entrega já foi encerrada")
    if new_status == f.status:
        return f
    if not await store_is_paid(db, order.id, store_id):
        raise NotPaidYet("O pagamento desta loja ainda não foi confirmado")
    if new_status != FulfillmentStatus.CANCELLED:
        if FULFILLMENT_PROGRESS[new_status] < FULFILLMENT_PROGRESS[f.status]:
            raise InvalidTransition("Não é possível voltar um status")
    f.status = new_status
    await db.commit()
    await sync_order_status(db, order)
    return f
