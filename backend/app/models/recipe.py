"""Receitas curadas (RN-020). Cada ingrediente aponta para um produto do catálogo;
``quantity`` é o número de embalagens para ``base_servings`` porções.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Recipe(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipes"

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    emoji: Mapped[str] = mapped_column(String(8), default="🍽️", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_servings: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    prep_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    steps: Mapped[str | None] = mapped_column(Text, nullable=True)  # um passo por linha

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", lazy="selectin"
    )


class RecipeIngredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Float, default=1, nullable=False)
    note: Mapped[str | None] = mapped_column(String(120), nullable=True)

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
