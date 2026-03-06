from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Optional


class PaginateBaseResponse(BaseModel):
    total_count: int = Field(..., description="Total count")
    total_pages: int = Field(..., description="Total pages")
    limit: int = Field(..., description="Limit")
    offset: int = Field(..., description="Offset")

class ListDocumnentRequest(BaseModel):
    document_type_id: Optional[str] = None
    status: Optional[str] = None
    keyword: Optional[str] = None
    order_by: str = Field(default="-created_at")
    offset: int = Field(default=0)
    limit: int = Field(default=50)

class DocumentBase(BaseModel):
    id: str = Field(...)
    document_type_id: str = Field(...)
    year: Optional[int] = None
    month: Optional[int] = None
    marriage_reg_no: Optional[str] = None
    marriage_date: Optional[str] = None
    sender: Optional[str] = None
    # Người/đơn vị nhận chính
    receiver: Optional[str] = None
    current_version_id: Optional[str] = None
    version_no:  int = Field(default=1)
    status: Optional[str] = None
    # Đường dẫn file scan gốc
    file_uri_original: Optional[str] = None
    # File đã qua xử lý
    file_uri_processed: Optional[str] = None
    # Toàn bộ text OCR raw, Dùng để search fulltext
    ocr_text: Optional[str] = None
    # JSON cấu trúc kết quả OCR
    ocr_json: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    # thêm cmnd/cccd (để nullable vì OCR có thể chưa extract được)
    cmnd: Optional[str] = None
    cccd: Optional[str] = None
    created_by: Optional[int] = None
    created_at:  Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(DocumentBase):
    document_type_name: Optional[str] = None
    image_base64: Optional[str] = None


class ListDocumnentsResponse(PaginateBaseResponse):
    data: Optional[List[DocumentResponse]] = []


class UpdateDocumentRequest(BaseModel):
    document_type_id: str = Field(..., max_length=36)
    marriage_date: datetime = Field(None)
    marriage_reg_no: Optional[str] = Field(None, max_length=100)
    sender: Optional[str] = Field(None, max_length=255)
    receiver: Optional[str] = Field(None, max_length=255)
    ocr_text: Optional[str] = None
    cmnd: Optional[str] = Field(None, max_length=20)
    cccd: Optional[str] = Field(None, max_length=20)

class UpdateStatus(BaseModel):
    status: str = Field(..., max_length=10, example="SUCCESS")
    