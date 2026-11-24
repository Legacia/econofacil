"""Listas de compras permanentes do usuário (RN-020)."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ShoppingList(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shopping_lists"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    items: Mapped[list["ShoppingListItem"]] = relationship(
        back_populates="shopping_list", cascade="all, delete-orphan", lazy="selectin"
    )


class ShoppingListItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shopping_list_items"
    __table_args__ = (UniqueConstraint("list_id", "product_id", name="uq_list_product"),)

    list_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shopping_lists.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    shopping_list: Mapped[ShoppingList] = relationship(back_populates="items")
