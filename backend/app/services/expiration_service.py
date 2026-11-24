"""Expirações centralizadas (RN-021): carrinhos, promoções e cobranças Pix.

Executada pelo agendador em segundo plano (``app/core/scheduler.py``) e, sob demanda,
por um administrador (``POST /admin/expirations/run``). É idempotente.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartStatus
from app.models.order import FulfillmentStatus, Order, OrderStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.promotion import Promotion, PromotionStatus
from app.services import merchant_service


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def expire_carts(db: AsyncSession) -> int:
    now = _now()
    carts = (await db.execute(select(Cart).where(Cart.status == CartStatus.ACTIVE))).scalars().all()
    n = 0
    for cart in carts:
        if _aware(cart.expires_at) <= now:
            cart.status = CartStatus.EXPIRED
            n += 1
    if n:
        await db.commit()
    return n


async def expire_promotions(db: AsyncSession) -> int:
    """Encerra promoções vencidas e restaura o preço-base da oferta."""
    now = _now()
    promos = (await db.execute(
        select(Promotion).where(Promotion.status == PromotionStatus.ACTIVE)
    )).scalars().all()
    n = 0
    for promo in promos:
        if _aware(promo.ends_at) <= now:
            offer = await merchant_service._get_offer(db, promo.store_id, promo.product_id)
            if offer is not None:
                offer.price = promo.base_price
                offer.original_price = None
            promo.status = PromotionStatus.ENDED
            n += 1
    if n:
        await db.commit()
    return n


async def expire_pix(db: AsyncSession) -> dict:
    """Cobranças Pix vencidas viram ``expired``; o pedido que ainda aguardava pagamento
    é cancelado (e as demais cobranças pendentes dele também)."""
    now = _now()
    pending = (await db.execute(
        select(Payment).where(
            Payment.status == PaymentStatus.PENDING, Payment.method == PaymentMethod.PIX
        )
    )).scalars().all()
    expired_payments = 0
    order_ids = set()
    for pay in pending:
        if pay.expires_at is not None and _aware(pay.expires_at) <= now:
            pay.status = PaymentStatus.EXPIRED
            expired_payments += 1
            order_ids.add(pay.order_id)

    cancelled_orders = 0
    for oid in order_ids:
        order = await db.get(Order, oid)
        if order is None or order.status != OrderStatus.AWAITING_PAYMENT:
            continue
        order.status = OrderStatus.CANCELLED
        for f in order.fulfillments:
            f.status = FulfillmentStatus.CANCELLED
        others = (await db.execute(
            select(Payment).where(Payment.order_id == oid, Payment.status == PaymentStatus.PENDING)
        )).scalars().all()
        for other in others:
            other.status = PaymentStatus.CANCELLED
        cancelled_orders += 1
    if expired_payments:
        await db.commit()
    return {"payments_expired": expired_payments, "orders_cancelled": cancelled_orders}


async def run_expirations(db: AsyncSession) -> dict:
    pix = await expire_pix(db)
    return {
        "carts_expired": await expire_carts(db),
        "promotions_ended": await expire_promotions(db),
        **pix,
    }
