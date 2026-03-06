from __future__ import annotations
from typing import Any, Optional
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Index,
    Text,
    DateTime,
    String,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import MEDIUMTEXT  # hoặc MEDIUMTEXT, LONGTEXT
from app.utils.utilities import gen_uuid

from app.models.base import Base

class DocumentField(Base):
    __tablename__ = "document_fields"
    __table_args__ = (
        Index("ix_doc_fields_doc_key", "document_id", "field_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)

    field_key: Mapped[str] = mapped_column(String(120), nullable=False)   # spouse_name
    field_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    image_base64: Mapped[Optional[str]] = mapped_column(MEDIUMTEXT, nullable=True)
    image_content_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # image/png, image/jpeg

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
