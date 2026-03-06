from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import Settings

from app.utils.utilities import gen_uuid

settings = Settings()
from .base import BaseModel


class Ward(BaseModel):
    __tablename__ = "wards"
    __table_args__ = (
        UniqueConstraint("database_name", "ward_key", name="uq_wards_database_name_ward_key"),
        Index("ix_wards_province_id", "province_id"),
        Index("ix_wards_ward_name", "ward_name"),
        {"schema": settings.common_db_name},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    database_name: Mapped[str] = mapped_column(String(64), nullable=False)

    province_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{settings.common_db_name}.provinces.id", ondelete="CASCADE"),
        nullable=False,
    )

    ward_key: Mapped[str] = mapped_column(String(20), nullable=False)
    ward_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    province = relationship(
        "Province",
        primaryjoin="Ward.province_id == Province.id",
        viewonly=True,
    )
