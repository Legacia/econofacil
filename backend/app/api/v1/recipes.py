"""Endpoints de receitas (/recipes) — RN-020."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.cart import _build_view
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.schemas.cart import CartView
from app.schemas.recipe import AddRecipeToCart, RecipeDetail, RecipeSummary
from app.services import cart_service, recipe_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/recipes", tags=["recipes"])
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[RecipeSummary])
async def list_recipes(db: DbSession):
    return await recipe_service.list_recipes(db)


@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe(
    recipe_id: uuid.UUID, db: DbSession, servings: Annotated[int | None, Query(ge=1, le=100)] = None
):
    recipe = await recipe_service.get_recipe(db, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    return await recipe_service.detail(db, recipe, servings)


@router.post("/{recipe_id}/add-to-cart", response_model=CartView)
async def add_recipe_to_cart(
    recipe_id: uuid.UUID, payload: AddRecipeToCart, db: DbSession, user: CurrentUser
):
    recipe = await recipe_service.get_recipe(db, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    cart = await cart_service.get_active_cart(db, user)
    cart = await recipe_service.add_to_cart(db, cart, recipe, payload.servings)
    await log_action(db, action="recipe.add_to_cart", user_id=user.id, entity=str(recipe_id))
    return await _build_view(db, cart)
