"""Endpoints de carrinho (/cart)."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.catalog import Product
from app.schemas.cart import (
    AddItemRequest,
    CartItemView,
    CartView,
    CheckoutRequest,
    OptimizeResult,
    OrderView,
    SetQuantityRequest,
)
from app.services import cart_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/cart", tags=["cart"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def _build_view(db: AsyncSession, cart) -> CartView:
    pids = [i.product_id for i in cart.items]
    products = {
        p.id: p
        for p in (await db.execute(select(Product).where(Product.id.in_(pids)))).scalars().all()
    }
    offers = await cart_service.gather_offers(db, pids)

    items: list[CartItemView] = []
    subtotal = 0.0
    qty_total = 0
    for i in cart.items:
        p = products.get(i.product_id)
        if p is None:
            continue
        store_offers = offers.get(i.product_id)
        best = min((o["price"] for o in store_offers.values()), default=None) if store_offers else None
        if best is not None:
            subtotal += best * i.quantity
        qty_total += i.quantity
        items.append(CartItemView(
            product_id=p.id, name=p.name, brand=p.brand, image_url=p.image_url,
            package_size=p.package_size, package_unit=p.package_unit,
            quantity=i.quantity, best_price=best, available=best is not None,
        ))
    return CartView(
        id=cart.id, expires_at=cart.expires_at, item_count=qty_total,
        subtotal_estimate=round(subtotal, 2), items=items,
    )


@router.get("", response_model=CartView)
async def get_cart(db: DbSession, user: CurrentUser):
    cart = await cart_service.get_active_cart(db, user)
    return await _build_view(db, cart)


@router.post("/items", response_model=CartView)
async def add_item(payload: AddItemRequest, db: DbSession, user: CurrentUser):
    cart = await cart_service.get_active_cart(db, user)
    try:
        cart = await cart_service.add_item(db, cart, payload.product_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return await _build_view(db, cart)


@router.patch("/items/{product_id}", response_model=CartView)
async def set_quantity(product_id: uuid.UUID, payload: SetQuantityRequest, db: DbSession, user: CurrentUser):
    cart = await cart_service.get_active_cart(db, user)
    try:
        cart = await cart_service.set_item_quantity(db, cart, product_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return await _build_view(db, cart)


@router.delete("/items/{product_id}", response_model=CartView)
async def remove_item(product_id: uuid.UUID, db: DbSession, user: CurrentUser):
    cart = await cart_service.get_active_cart(db, user)
    cart = await cart_service.remove_item(db, cart, product_id)
    return await _build_view(db, cart)


@router.delete("", response_model=CartView)
async def clear_cart(db: DbSession, user: CurrentUser):
    cart = await cart_service.get_active_cart(db, user)
    cart = await cart_service.clear(db, cart)
    return await _build_view(db, cart)


@router.get("/optimize", response_model=OptimizeResult)
async def optimize_cart(db: DbSession, user: CurrentUser):
    cart = await cart_service.get_active_cart(db, user)
    plan = await cart_service.optimize(db, cart)
    return OptimizeResult(**plan)


@router.post("/checkout", response_model=OrderView)
async def checkout(payload: CheckoutRequest, db: DbSession, user: CurrentUser):
    from app.models.payment import PaymentMethod
    from app.schemas.payment import PaymentView
    from app.services import payment_service

    method = PaymentMethod(payload.payment_method)
    if method == PaymentMethod.CARD:  # valida ANTES de criar o pedido
        raise HTTPException(status_code=422, detail="Pagamento com cartão ainda não disponível")

    cart = await cart_service.get_active_cart(db, user)
    try:
        order = await cart_service.checkout(db, user, cart, payload.strategy)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    payments = await payment_service.create_for_order(db, order, method)

    await log_action(db, action="cart.checkout", user_id=user.id, entity=order.code,
                     details={"strategy": payload.strategy, "savings": float(order.savings),
                              "payment_method": payload.payment_method})
    view = OrderView.model_validate(order)
    view.payments = [PaymentView.from_payment(p) for p in payments]
    return view
