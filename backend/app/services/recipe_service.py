"""Receitas (RN-020): detalhe com escala de porções e conversão em carrinho."""
from __future__ import annotations

import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart
from app.models.recipe import Recipe
from app.services import cart_service, pricing


def scale_quantity(quantity: float, base_servings: int, servings: int) -> int:
    """Embalagens necessárias para ``servings`` porções (arredonda para cima, mínimo 1)."""
    return max(1, math.ceil(round(quantity * servings / base_servings, 6)))


async def list_recipes(db: AsyncSession) -> list[dict]:
    recipes = (await db.execute(select(Recipe).order_by(Recipe.title))).scalars().all()
    all_pids = [i.product_id for r in recipes for i in r.ingredients]
    prices = await pricing.best_prices(db, all_pids)
    out = []
    for r in recipes:
        cost = sum(
            scale_quantity(i.quantity, r.base_servings, r.base_servings) * prices.get(i.product_id, 0.0)
            for i in r.ingredients
        )
        out.append({
            "id": r.id, "title": r.title, "emoji": r.emoji, "description": r.description,
            "base_servings": r.base_servings, "prep_minutes": r.prep_minutes,
            "ingredient_count": len(r.ingredients), "estimated_cost": round(cost, 2),
        })
    return out


async def get_recipe(db: AsyncSession, recipe_id: uuid.UUID) -> Recipe | None:
    return await db.get(Recipe, recipe_id)


async def detail(db: AsyncSession, recipe: Recipe, servings: int | None) -> dict:
    servings = servings or recipe.base_servings
    pids = [i.product_id for i in recipe.ingredients]
    prices = await pricing.best_prices(db, pids)
    products = await pricing.products_by_id(db, pids)
    rows, total = [], 0.0
    for ing in recipe.ingredients:
        prod = products.get(ing.product_id)
        if prod is None:
            continue
        qty = scale_quantity(ing.quantity, recipe.base_servings, servings)
        price = prices.get(ing.product_id)
        line = round(price * qty, 2) if price is not None else None
        total += line or 0.0
        rows.append({
            "product_id": prod.id, "name": prod.name,
            "package": f"{prod.package_size:g} {prod.package_unit}", "note": ing.note,
            "quantity": qty, "best_price": price, "line_estimate": line,
            "available": price is not None,
        })
    return {
        "id": recipe.id, "title": recipe.title, "emoji": recipe.emoji,
        "description": recipe.description, "base_servings": recipe.base_servings,
        "servings": servings, "prep_minutes": recipe.prep_minutes,
        "steps": [s for s in (recipe.steps or "").splitlines() if s.strip()],
        "ingredients": rows, "estimated_cost": round(total, 2),
        "cost_per_serving": round(total / servings, 2) if servings else 0.0,
    }


async def add_to_cart(db: AsyncSession, cart: Cart, recipe: Recipe, servings: int | None) -> Cart:
    servings = servings or recipe.base_servings
    for ing in recipe.ingredients:
        qty = scale_quantity(ing.quantity, recipe.base_servings, servings)
        cart = await cart_service.add_item(db, cart, ing.product_id, qty)
    return cart
