"""Auxiliares de preço compartilhados por receitas, listas e recomendações."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product, Store, StoreProduct


async def best_prices(db: AsyncSession, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, float]:
    """Menor preço de prateleira em estoque, entre as lojas ativas."""
    if not product_ids:
        return {}
    result = await db.execute(
        select(StoreProduct.product_id, func.min(StoreProduct.price))
        .join(Store, Store.id == StoreProduct.store_id)
        .where(
            StoreProduct.product_id.in_(product_ids),
            StoreProduct.in_stock.is_(True),
            Store.is_active.is_(True),
        )
        .group_by(StoreProduct.product_id)
    )
    return {pid: float(price) for pid, price in result.all()}


async def products_by_id(db: AsyncSession, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, Product]:
    if not product_ids:
        return {}
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    return {p.id: p for p in result.scalars().all()}
