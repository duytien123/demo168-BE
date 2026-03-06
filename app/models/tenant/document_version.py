from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    DateTime, ForeignKey, Index, Integer, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.utilities import gen_uuid


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        Index("ix_docver_doc_verno", "document_id", "version_no", unique=True),
        Index("ix_docver_doc_time", "document_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)

    version_no: Mapped[int] = mapped_column(Integer, nullable=False)  # 1,2,3...
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")

    file_uri_original: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_uri_processed: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)

    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
