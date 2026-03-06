from __future__ import annotations
from typing import Any
from sqlalchemy import (
    Boolean,
    Index,
    Integer,
    String,
    UniqueConstraint,
    JSON
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.utilities import gen_uuid

class DocumentType(Base):
    __tablename__ = "document_types"
    __table_args__ = (
        UniqueConstraint("type_key", "version", name="uq_doc_types_key_version"),
        Index("ix_doc_types_key", "type_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    type_key: Mapped[str] = mapped_column(String(120), nullable=False)  # marriage_certificate
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    schema_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
