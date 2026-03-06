from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.config import Settings

from app.utils.utilities import gen_uuid

settings = Settings()
from .base import BaseModel


class Province(BaseModel):
    __tablename__ = "provinces"
    __table_args__ = (
        UniqueConstraint("province_key", name="uq_provinces_province_key"),
        Index("ix_provinces_province_name", "province_name"),
        Index("ix_provinces_province_key", "province_key"),
        {"schema": settings.common_db_name},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    province_key: Mapped[str] = mapped_column(String(20), nullable=False)
    province_name: Mapped[str] = mapped_column(String(255), nullable=False)

    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=func.now(), onupdate=func.now()
    )
