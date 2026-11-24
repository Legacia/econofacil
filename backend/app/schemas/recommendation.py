"""Schemas das recomendações contextuais da Noor V2 (RN-023)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel


class RecommendationItem(BaseModel):
    product_id: uuid.UUID
    name: str
    package: str
    best_price: float | None = None
    score: int          # nº de pedidos que sustentam a recomendação
    reason: str         # texto pronto para a interface
