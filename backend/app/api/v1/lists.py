"""Endpoints de listas de compras (/lists) — RN-020."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.cart import _build_view
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.schemas.cart import CartView, OptimizeResult
from app.schemas.shopping_list import (
    ListCreate, ListDetail, ListItemAdd, ListItemUpdate, ListSummary,
)
from app.services import cart_service, shopping_list_service as svc

router = APIRouter(prefix="/lists", tags=["lists"])
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def _owned(db, user, list_id):
    sl = await svc.get_owned(db, user, list_id)
    if sl is None:
        raise HTTPException(status_code=404, detail="Lista não encontrada")
    return sl


@router.get("", response_model=list[ListSummary])
async def my_lists(db: DbSession, user: CurrentUser):
    return [await svc.summary(sl) for sl in await svc.list_for_user(db, user)]


@router.post("", response_model=ListDetail, status_code=status.HTTP_201_CREATED)
async def create_list(payload: ListCreate, db: DbSession, user: CurrentUser):
    try:
        sl = await svc.create(db, user, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return await svc.detail(db, sl)


@router.get("/{list_id}", response_model=ListDetail)
async def get_list(list_id: uuid.UUID, db: DbSession, user: CurrentUser):
    return await svc.detail(db, await _owned(db, user, list_id))


@router.patch("/{list_id}", response_model=ListDetail)
async def rename_list(list_id: uuid.UUID, payload: ListCreate, db: DbSession, user: CurrentUser):
    sl = await svc.rename(db, await _owned(db, user, list_id), payload.name)
    return await svc.detail(db, sl)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(list_id: uuid.UUID, db: DbSession, user: CurrentUser):
    await svc.delete(db, await _owned(db, user, list_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{list_id}/items", response_model=ListDetail)
async def add_list_item(list_id: uuid.UUID, payload: ListItemAdd, db: DbSession, user: CurrentUser):
    sl = await _owned(db, user, list_id)
    try:
        sl = await svc.add_item(db, sl, payload.product_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return await svc.detail(db, sl)


@router.patch("/{list_id}/items/{product_id}", response_model=ListDetail)
async def update_list_item(
    list_id: uuid.UUID, product_id: uuid.UUID, payload: ListItemUpdate, db: DbSession, user: CurrentUser
):
    sl = await _owned(db, user, list_id)
    try:
        sl = await svc.update_item(db, sl, product_id, payload.quantity, payload.checked)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return await svc.detail(db, sl)


@router.delete("/{list_id}/items/{product_id}", response_model=ListDetail)
async def remove_list_item(list_id: uuid.UUID, product_id: uuid.UUID, db: DbSession, user: CurrentUser):
    sl = await svc.remove_item(db, await _owned(db, user, list_id), product_id)
    return await svc.detail(db, sl)


@router.get("/{list_id}/compare", response_model=OptimizeResult)
async def compare_list(list_id: uuid.UUID, db: DbSession, user: CurrentUser):
    sl = await _owned(db, user, list_id)
    try:
        plan = await svc.compare(db, sl)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return OptimizeResult(**plan)


@router.post("/{list_id}/to-cart", response_model=CartView)
async def list_to_cart(list_id: uuid.UUID, db: DbSession, user: CurrentUser):
    sl = await _owned(db, user, list_id)
    lines = svc.pending_lines(sl)
    if not lines:
        raise HTTPException(status_code=400, detail="A lista não tem itens pendentes")
    cart = await cart_service.get_active_cart(db, user)
    for pid, qty in lines:
        cart = await cart_service.add_item(db, cart, pid, qty)
    return await _build_view(db, cart)
