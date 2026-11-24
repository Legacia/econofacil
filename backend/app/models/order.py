"""Modelos de pedido. Os itens guardam um *snapshot* de nome e preço para que
o histórico permaneça íntegro mesmo se o catálogo mudar depois."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OrderStatus(str, enum.Enum):
    AWAITING_PAYMENT = "awaiting_payment"
    PLACED = "placed"
    SEPARATING = "separating"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class FulfillmentStatus(str, enum.Enum):
    """Andamento de UMA loja dentro do pedido (RN-019)."""
    PLACED = "placed"
    SEPARATING = "separating"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ordem de progresso (usada para derivar o status do pedido: vale o MAIS LENTO)
FULFILLMENT_PROGRESS = {
    FulfillmentStatus.PLACED: 0,
    FulfillmentStatus.SEPARATING: 1,
    FulfillmentStatus.ON_THE_WAY: 2,
    FulfillmentStatus.DELIVERED: 3,
}


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20),
        default=OrderStatus.PLACED,
        nullable=False,
    )
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    savings: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    store_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )
    fulfillments: Mapped[list["OrderFulfillment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin",
        order_by="OrderFulfillment.store_name",
    )


class OrderFulfillment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Status independente de cada loja do pedido (RN-019)."""

    __tablename__ = "order_fulfillments"
    __table_args__ = (UniqueConstraint("order_id", "store_id", name="uq_fulfillment_order_store"),)

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    store_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    store_name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[FulfillmentStatus] = mapped_column(
        Enum(FulfillmentStatus, native_enum=False, length=20),
        default=FulfillmentStatus.PLACED, nullable=False,
    )
    order: Mapped[Order] = relationship(back_populates="fulfillments")


class OrderItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # snapshots (não são FKs rígidas de propósito, mas guardamos os ids)
    store_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    store_name: Mapped[str] = mapped_column(String(160), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
