"""Schemas de receitas (RN-020)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class RecipeSummary(BaseModel):
    id: uuid.UUID
    title: str
    emoji: str
    description: str | None = None
    base_servings: int
    prep_minutes: int | None = None
    ingredient_count: int
    estimated_cost: float


class RecipeIngredientView(BaseModel):
    product_id: uuid.UUID
    name: str
    package: str
    note: str | None = None
    quantity: int                # embalagens, já ajustadas às porções
    best_price: float | None = None
    line_estimate: float | None = None
    available: bool


class RecipeDetail(BaseModel):
    id: uuid.UUID
    title: str
    emoji: str
    description: str | None = None
    base_servings: int
    servings: int
    prep_minutes: int | None = None
    steps: list[str]
    ingredients: list[RecipeIngredientView]
    estimated_cost: float
    cost_per_serving: float


class AddRecipeToCart(BaseModel):
    servings: int | None = Field(default=None, ge=1, le=100)
