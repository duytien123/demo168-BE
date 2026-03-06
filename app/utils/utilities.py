from datetime import date, datetime
import unicodedata
import re
import uuid
import json
from typing import Any, Dict, Optional, Tuple, Union
from sqlalchemy.inspection import inspect

def normalize_key(text: Optional[str]) -> str:
    if not text:
        return ""

    # Ép về string phòng trường hợp int/float
    text = str(text)

    # Chuẩn hóa Unicode
    text = unicodedata.normalize("NFD", text)

    # Bỏ dấu tiếng Việt
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # Chuyển đ -> d
    text = text.replace("đ", "d").replace("Đ", "D")

    # Lowercase
    text = text.lower()

    # Thay khoảng trắng bằng _
    text = re.sub(r"\s+", "_", text)

    # Bỏ ký tự đặc biệt (chỉ giữ a-z, 0-9, _)
    text = re.sub(r"[^a-z0-9_]", "", text)

    return text

def gen_uuid() -> str:
    return str(uuid.uuid4())

def to_dict(data: Any) -> Optional[Dict]:
    """
    Convert bất kỳ input nào về dict nếu có thể.
    - str JSON -> dict
    - bytes JSON -> dict
    - dict -> giữ nguyên
    - invalid -> return None
    """

    if data is None:
        return None

    # Nếu đã là dict
    if isinstance(data, dict):
        return data

    # Nếu là bytes
    if isinstance(data, bytes):
        try:
            data = data.decode("utf-8")
        except Exception:
            return None

    # Nếu là string -> parse json
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    return None


def sa_to_dict(obj) -> Dict[str, Any]:
    """Convert SQLAlchemy ORM instance -> dict (only columns)."""
    data = {}
    mapper = inspect(obj).mapper
    for col in mapper.column_attrs:
        v = getattr(obj, col.key)
        if isinstance(v, (datetime, date)):
            v = v.isoformat()
        data[col.key] = v
    return data


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None

    if isinstance(value, date):
        return value

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue

    return None

def parse_confidence(value: Any) -> Optional[float]:
    if value is None:
        return None

    # đã là số
    if isinstance(value, (int, float)):
        v = float(value)
    else:
        s = str(value).strip()
        if not s:
            return None

        # "87%" -> 0.87
        if s.endswith("%"):
            try:
                return float(s[:-1].strip()) / 100
            except ValueError:
                return None

        # "0,87" -> "0.87"
        s = s.replace(",", ".")
        try:
            v = float(s)
        except ValueError:
            return None

    # nếu OCR trả 87 thay vì 0.87, tự normalize về 0..1
    if v > 1.0:
        v = v / 100.0

    # clamp 0..1
    if v < 0:
        v = 0.0
    if v > 1:
        v = 1.0

    return v

def parse_ocr_data(data: dict, ocr_key: str):
    val = None
    if not data:
        return None

    value = data.get(ocr_key)
    if value is None:
        return None

    # Trường hợp string
    if isinstance(value, str):
        return value

    # Trường hợp dict {"label": "...", "value": "..."}
    if isinstance(value, dict):
        val = value.get("value")
        return val

    return val

def parse_ocr_data_to_label_value(data: dict, ocr_key: str):
    if not data:
        return ocr_key, None

    label, val = ocr_key, None
    value = data.get(ocr_key)
    if value is None:
        return label, val

    # Trường hợp string
    if isinstance(value, str):
        return ocr_key, value

    # Trường hợp dict {"label": "...", "value": "..."}
    if isinstance(value, dict):
        label = value.get("label") or ocr_key
        val = value.get("value")
        return label, val

    return label, val


def make_data_url(b64: Optional[str], content_type: Optional[str]) -> Optional[str]:
    if not b64 or not content_type:
        return None
    return f"data:{content_type};base64,{b64}"


UPDATE_FIELDS = {
    "document_type_id",
    "year",
    "month",
    "marriage_reg_no",
    "marriage_date",
    "sender",
    "receiver",
    "status",
    "file_uri_original",
    "file_uri_processed",
    "ocr_text",
    "ocr_json",
    "confidence",
    "cmnd",
    "cccd",
}

def merge_document(document, params, *, ignore_none: bool = True) -> Any:
    """
    Merge params vào document (ORM instance).
    - ignore_none=True: field nào = None thì bỏ qua (không update)
    """
    # Pydantic v1: params.dict(exclude_unset=True)
    # Pydantic v2: params.model_dump(exclude_unset=True)
    if hasattr(params, "model_dump"):
        payload = params.model_dump(exclude_unset=True)
    else:
        payload = params.dict(exclude_unset=True)

    for key, val in payload.items():
        if key not in UPDATE_FIELDS:
            continue
        if ignore_none and val is None:
            continue
        setattr(document, key, val)

    return document
