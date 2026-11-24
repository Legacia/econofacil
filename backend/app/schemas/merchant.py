"""Schemas do Portal do Comerciante."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import FulfillmentStatus, OrderStatus
from app.models.promotion import PromotionStatus


# --------------------------------------------------------------------------- #
# Inventário
# --------------------------------------------------------------------------- #
class InventoryRow(BaseModel):
    product_id: uuid.UUID
    product_name: str
    package_size: float
    package_unit: str
    price: float
    original_price: float | None = None
    in_stock: bool
    stock_quantity: int | None = None


# --------------------------------------------------------------------------- #
# Promoções
# --------------------------------------------------------------------------- #
class PromotionCreate(BaseModel):
    product_id: uuid.UUID
    promo_price: float = Field(gt=0)
    ends_at: datetime


class PromotionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    store_id: uuid.UUID
    product_id: uuid.UUID
    promo_price: float
    base_price: float
    ends_at: datetime
    status: PromotionStatus


# --------------------------------------------------------------------------- #
# Pedidos do comerciante
# --------------------------------------------------------------------------- #
class MerchantOrderLine(BaseModel):
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class MerchantOrder(BaseModel):
    """Visão da loja sobre um pedido: ``status`` é o andamento DESTA loja (RN-019)."""
    order_id: uuid.UUID
    code: str
    status: FulfillmentStatus
    order_status: OrderStatus
    store_id: uuid.UUID
    store_name: str
    paid: bool
    created_at: datetime
    store_subtotal: float
    items: list[MerchantOrderLine]


class OrderStatusUpdate(BaseModel):
    status: FulfillmentStatus
    store_id: uuid.UUID | None = None


# --------------------------------------------------------------------------- #
# Relatório
# --------------------------------------------------------------------------- #
class TopProduct(BaseModel):
    product_name: str
    quantity: int
    revenue: float


class StoreReport(BaseModel):
    orders_count: int
    revenue: float
    units_sold: int
    top_products: list[TopProduct]


# --------------------------------------------------------------------------- #
# Loja do comerciante (inclui a chave Pix própria — RN-022)
# --------------------------------------------------------------------------- #
class MerchantStoreView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    pix_key: str | None = None


class StorePixUpdate(BaseModel):
    # vazio/None remove a chave própria (volta a usar a chave da plataforma)
    pix_key: str | None = Field(default=None, max_length=77, pattern=r"^\S*$")
