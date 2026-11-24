"""Listas de compras permanentes (RN-020), com escopo do dono."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.user import User
from app.services import cart_service, pricing

MAX_LISTS_PER_USER = 50


async def list_for_user(db: AsyncSession, user: User) -> list[ShoppingList]:
    result = await db.execute(
        select(ShoppingList).where(ShoppingList.user_id == user.id).order_by(ShoppingList.created_at)
    )
    return list(result.scalars().all())


async def get_owned(db: AsyncSession, user: User, list_id: uuid.UUID) -> ShoppingList | None:
    sl = await db.get(ShoppingList, list_id)
    if sl is None or sl.user_id != user.id:
        return None  # 404 também para listas de outros (não vaza existência)
    return sl


async def create(db: AsyncSession, user: User, name: str) -> ShoppingList:
    if len(await list_for_user(db, user)) >= MAX_LISTS_PER_USER:
        raise ValueError("Limite de listas atingido")
    sl = ShoppingList(user_id=user.id, name=name.strip())
    db.add(sl)
    await db.commit()
    await db.refresh(sl)
    return sl


async def rename(db: AsyncSession, sl: ShoppingList, name: str) -> ShoppingList:
    sl.name = name.strip()
    await db.commit()
    await db.refresh(sl)
    return sl


async def delete(db: AsyncSession, sl: ShoppingList) -> None:
    await db.delete(sl)
    await db.commit()


async def add_item(db: AsyncSession, sl: ShoppingList, product_id: uuid.UUID, quantity: int) -> ShoppingList:
    if await db.get(Product, product_id) is None:
        raise ValueError("Produto não encontrado")
    existing = next((i for i in sl.items if i.product_id == product_id), None)
    if existing:
        existing.quantity += quantity
        existing.checked = False
    else:
        db.add(ShoppingListItem(list_id=sl.id, product_id=product_id, quantity=quantity))
    await db.commit()
    await db.refresh(sl)
    return sl


async def update_item(
    db: AsyncSession, sl: ShoppingList, product_id: uuid.UUID,
    quantity: int | None, checked: bool | None,
) -> ShoppingList:
    item = next((i for i in sl.items if i.product_id == product_id), None)
    if item is None:
        raise LookupError("Item não está na lista")
    if quantity is not None:
        item.quantity = quantity
    if checked is not None:
        item.checked = checked
    await db.commit()
    await db.refresh(sl)
    return sl


async def remove_item(db: AsyncSession, sl: ShoppingList, product_id: uuid.UUID) -> ShoppingList:
    item = next((i for i in sl.items if i.product_id == product_id), None)
    if item is not None:
        await db.delete(item)
        await db.commit()
        await db.refresh(sl)
    return sl


def pending_lines(sl: ShoppingList) -> list[tuple[uuid.UUID, int]]:
    return [(i.product_id, i.quantity) for i in sl.items if not i.checked]


async def summary(sl: ShoppingList) -> dict:
    return {
        "id": sl.id, "name": sl.name, "item_count": len(sl.items),
        "checked_count": sum(1 for i in sl.items if i.checked),
    }


async def detail(db: AsyncSession, sl: ShoppingList) -> dict:
    pids = [i.product_id for i in sl.items]
    prices = await pricing.best_prices(db, pids)
    products = await pricing.products_by_id(db, pids)
    rows, total = [], 0.0
    for i in sorted(sl.items, key=lambda x: (x.checked, products[x.product_id].name if x.product_id in products else "")):
        p = products.get(i.product_id)
        if p is None:
            continue
        price = prices.get(i.product_id)
        if price is not None and not i.checked:
            total += price * i.quantity
        rows.append({
            "product_id": p.id, "name": p.name, "package": f"{p.package_size:g} {p.package_unit}",
            "quantity": i.quantity, "checked": i.checked, "best_price": price,
        })
    return {**await summary(sl), "estimated_total": round(total, 2), "items": rows}


async def compare(db: AsyncSession, sl: ShoppingList) -> dict:
    """Compara a lista inteira (itens pendentes) — loja única × split (RN-018)."""
    lines = pending_lines(sl)
    if not lines:
        raise ValueError("A lista não tem itens pendentes para comparar")
    return await cart_service.optimize_lines(db, lines)
