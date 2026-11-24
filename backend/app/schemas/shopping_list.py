"""Schemas de listas de compras (RN-020)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ListItemAdd(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=999)


class ListItemUpdate(BaseModel):
    quantity: int | None = Field(default=None, ge=1, le=999)
    checked: bool | None = None


class ListItemView(BaseModel):
    product_id: uuid.UUID
    name: str
    package: str
    quantity: int
    checked: bool
    best_price: float | None = None


class ListSummary(BaseModel):
    id: uuid.UUID
    name: str
    item_count: int
    checked_count: int


class ListDetail(ListSummary):
    estimated_total: float
    items: list[ListItemView]
