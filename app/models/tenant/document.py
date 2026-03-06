from __future__ import annotations
from typing import Any, Optional
from datetime import datetime, date
from sqlalchemy import (
    Index,
    Text,
    Integer,
    DateTime,
    String,
    ForeignKey,
    JSON,
    Date
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

from app.utils.utilities import gen_uuid

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_docs_created", "created_at"),
        Index("ix_docs_type_year", "document_type_id", "year"),
        Index("ix_docs_type_year_month", "document_type_id", "year", "month"),
        Index("ix_docs_cccd", "cccd"),
        Index("ix_docs_cmnd", "cmnd"),
        Index("ix_docs_marriage_reg_no", "marriage_reg_no"),
        Index("ix_docs_cccd_marriage_date", "cccd", "marriage_date"),
        Index("ix_docs_sender", "sender"),
        Index("ix_docs_receiver", "receiver"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    # Loại tài liệu
    document_type_id: Mapped[str] = mapped_column(ForeignKey("document_types.id"), nullable=False)

    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1..12

    # số pháp lý của giấy
    marriage_reg_no: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    # Ngày đăng ký
    marriage_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Người gửi (có thể là cơ quan hoặc cá nhân)
    sender: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Người/đơn vị nhận chính
    receiver: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    

    current_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    status: Mapped[str] = mapped_column(String(30), default="PENDING")

    # Đường dẫn file scan gốc
    file_uri_original: Mapped[str] = mapped_column(String(500))
    # File đã qua xử lý
    file_uri_processed: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Toàn bộ text OCR raw, Dùng để search fulltext
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON cấu trúc kết quả OCR
    ocr_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    confidence: Mapped[Optional[float]] = mapped_column(nullable=True) # Độ tin cậy tổng thể của document Ví dụ: 0.87

    # thêm cmnd/cccd (để nullable vì OCR có thể chưa extract được)
    cmnd: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # CMND 9 số (có thể có space)
    cccd: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # CCCD 12 số

    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
