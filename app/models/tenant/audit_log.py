from __future__ import annotations

from typing import Any, Optional
from datetime import datetime
from sqlalchemy import (
    Index,
    DateTime,
    String,
    ForeignKey,
    JSON,
    Integer
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_time", "created_at"),
        Index("ix_audit_doc", "document_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    document_id: Mapped[Optional[str]] = mapped_column(ForeignKey("documents.id"), nullable=True)

    action: Mapped[str] = mapped_column(String(50))  # UPLOAD, EDIT_FIELD, APPROVE...
    detail_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
