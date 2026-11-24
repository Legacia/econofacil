"""Noor V2 — recomendações contextuais (RN-023).

* ``also_bought``  — "quem comprou este também comprou": co-ocorrência em pedidos.
  Usa apenas contagens AGREGADAS de pedidos (nada de dados pessoais é exposto).
* ``usual``        — "você costuma comprar": produtos que o usuário já comprou em
  vários pedidos e que NÃO estão no carrinho ativo agora.
Pedidos cancelados não contam.
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartStatus
from app.models.catalog import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.services import pricing

RECO_VERSION = "noor-reco-1.0.0"


async def _decorate(db, rows, reason_fn) -> list[dict]:
    pids = [pid for pid, _ in rows]
    products = await pricing.products_by_id(db, pids)
    prices = await pricing.best_prices(db, pids)
    out = []
    for pid, score in rows:
        p = products.get(pid)
        if p is None or pid not in prices:  # só recomenda o que dá para comprar agora
            continue
        out.append({
            "product_id": pid, "name": p.name, "package": f"{p.package_size:g} {p.package_unit}",
            "best_price": prices[pid], "score": int(score), "reason": reason_fn(int(score)),
        })
    return out


async def also_bought(db: AsyncSession, product_id: uuid.UUID, limit: int = 5) -> list[dict]:
    with_product = (
        select(OrderItem.order_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(OrderItem.product_id == product_id, Order.status != OrderStatus.CANCELLED)
    )
    count = func.count(func.distinct(OrderItem.order_id))
    rows = (await db.execute(
        select(OrderItem.product_id, count)
        .join(Product, Product.id == OrderItem.product_id)
        .where(OrderItem.order_id.in_(with_product), OrderItem.product_id != product_id)
        .group_by(OrderItem.product_id, Product.name)
        .order_by(count.desc(), Product.name, OrderItem.product_id)  # desempate estável
        .limit(limit * 3)  # folga para descartar itens sem oferta
    )).all()
    items = await _decorate(
        db, rows,
        lambda n: f"Comprado junto em {n} pedido{'s' if n != 1 else ''}",
    )
    return items[:limit]


async def usual(db: AsyncSession, user: User, limit: int = 6, min_orders: int = 2) -> list[dict]:
    cart = (await db.execute(
        select(Cart).where(Cart.user_id == user.id, Cart.status == CartStatus.ACTIVE)
    )).scalar_one_or_none()
    in_cart = {i.product_id for i in cart.items} if cart else set()

    count = func.count(func.distinct(OrderItem.order_id))
    last = func.max(Order.created_at)
    rows = (await db.execute(
        select(OrderItem.product_id, count)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.user_id == user.id, Order.status != OrderStatus.CANCELLED)
        .group_by(OrderItem.product_id)
        .having(count >= min_orders)
        .order_by(count.desc(), last.desc())
    )).all()
    rows = [(pid, n) for pid, n in rows if pid not in in_cart]
    items = await _decorate(db, rows, lambda n: f"Você comprou {n} vezes")
    return items[:limit]
