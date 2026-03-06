from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.utilities import gen_uuid


class DocumentFieldVersion(Base):
    __tablename__ = "document_field_versions"
    __table_args__ = (
        Index("ix_docfver_ver_key", "version_id", "field_key"),
        Index("ix_docfver_key", "field_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id"), nullable=False)

    field_key: Mapped[str] = mapped_column(String(120), nullable=False)
    field_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    source_bbox_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
