"""Serviço de pagamentos: um pagamento POR LOJA (RN-022), confirmação e consulta."""
from __future__ import annotations

import re
import unicodedata
import uuid
from collections import OrderedDict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Store
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.user import User
from app.payments.provider import get_pix_provider
from app.services import order_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ascii(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()


def _store_totals(order: Order) -> "OrderedDict[uuid.UUID, tuple[str, float]]":
    totals: "OrderedDict[uuid.UUID, tuple[str, float]]" = OrderedDict()
    for item in order.items:
        name, acc = totals.get(item.store_id, (item.store_name, 0.0))
        totals[item.store_id] = (name, round(acc + float(item.line_total), 2))
    return totals


async def create_for_order(db: AsyncSession, order: Order, method: PaymentMethod) -> list[Payment]:
    """Cria um pagamento para cada loja do pedido, com o valor daquela loja."""
    if method == PaymentMethod.CARD:
        raise ValueError("Pagamento com cartão ainda não disponível")

    payments: list[Payment] = []
    for idx, (store_id, (store_name, amount)) in enumerate(_store_totals(order).items(), start=1):
        if method == PaymentMethod.PIX:
            store = await db.get(Store, store_id)
            store_key = store.pix_key if store is not None and store.pix_key else None
            charge = get_pix_provider().create_charge(
                amount=amount,
                txid=f"{order.code}L{idx}",
                pix_key=store_key,
                merchant_name=_ascii(store_name) if store_key else None,
            )
            payment = Payment(
                order_id=order.id, store_id=store_id, store_name=store_name, method=method,
                status=PaymentStatus.PENDING, amount=amount, provider=charge.provider,
                txid=charge.txid, br_code=charge.br_code, qr_svg=charge.qr_svg,
                expires_at=charge.expires_at,
            )
        else:  # ECONOPAY — carteira do ecossistema, liquidação imediata (stub)
            payment = Payment(
                order_id=order.id, store_id=store_id, store_name=store_name, method=method,
                status=PaymentStatus.PAID, amount=amount, provider="econopay-wallet",
                paid_at=_utcnow(),
            )
        db.add(payment)
        payments.append(payment)
    await db.commit()
    for p in payments:
        await db.refresh(p)
    await order_service.sync_order_status(db, order)
    return payments


async def get_for_order(db: AsyncSession, order_id: uuid.UUID) -> list[Payment]:
    return await order_service.payments_of(db, order_id)


async def get_payment(db: AsyncSession, user: User, payment_id: uuid.UUID) -> Payment | None:
    payment = await db.get(Payment, payment_id)
    if payment is None:
        return None
    order = await db.get(Order, payment.order_id)
    if order is None or order.user_id != user.id:
        return None
    return payment


async def confirm_pix(db: AsyncSession, txid: str) -> Payment | None:
    """Confirma UM pagamento Pix (callback do PSP, idempotente). Quando todas as lojas
    estiverem pagas, o pedido passa a ``placed``."""
    result = await db.execute(select(Payment).where(Payment.txid == txid))
    payment = result.scalar_one_or_none()
    if payment is None:
        return None
    if payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.PAID
        payment.paid_at = _utcnow()
        await db.commit()
        order = await db.get(Order, payment.order_id)
        if order is not None and order.status != OrderStatus.CANCELLED:
            await order_service.sync_order_status(db, order)
        await db.refresh(payment)
    return payment
