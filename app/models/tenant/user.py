from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    String,
    DateTime,
    Integer
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Thông tin đăng nhập
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Phân quyền
    role: Mapped[str] = mapped_column(String(30), default="WARD_USER")
    # WARD_USER / WARD_ADMIN / PROVINCE_ADMIN / SUPER_ADMIN

    # Trạng thái
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    # ACTIVE / INACTIVE / LOCKED

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Thời gian
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
