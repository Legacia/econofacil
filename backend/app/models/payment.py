"""Modelo de pagamento (um por LOJA do pedido — RN-022: liquidação por loja)."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PaymentMethod(str, enum.Enum):
    PIX = "pix"
    ECONOPAY = "econopay"
    CARD = "card"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # loja recebedora (RN-022)
    store_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True)
    store_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=12), nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=12),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)

    # específicos de Pix
    txid: Mapped[str | None] = mapped_column(String(35), unique=True, index=True, nullable=True)
    br_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_svg: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
