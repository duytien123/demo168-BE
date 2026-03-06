import json
import re
from datetime import datetime, date
from typing import Any, Dict, Optional, Union, Literal


FieldName = Literal[
    "marriage_date",
    "marriage_reg_no",
    "year",
    "month",
    "sender",
    "receiver",
    "ocr_text",
    "confidence",
    "cmnd",
    "cccd",
    "document_type"
]


def _to_dict_if_json_str(data: Any) -> Optional[Dict[str, Any]]:
    if data is None:
        return None
    if isinstance(data, dict):
        return data
    if isinstance(data, (bytes, bytearray)):
        try:
            data = data.decode("utf-8")
        except Exception:
            return None
    if isinstance(data, str):
        s = data.strip()
        if not s:
            return None
        try:
            obj = json.loads(s)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def _extract_value(raw: Any) -> Any:
    """
    OCR có thể trả:
    - "Công văn"
    - {"label": "...", "value": "..."}
    - None
    """
    if raw is None:
        return None
    if isinstance(raw, dict):
        if "value" in raw:
            return raw.get("value")
        return raw  # nếu dict thường
    return raw


def _parse_int(value: Any, *, min_v: int | None = None, max_v: int | None = None) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        v = value
    elif isinstance(value, float):
        if not value.is_integer():
            return None
        v = int(value)
    else:
        s = str(value).strip()
        if not s:
            return None
        # lấy số đầu tiên trong chuỗi (vd "2025年" -> 2025)
        m = re.search(r"-?\d+", s)
        if not m:
            return None
        try:
            v = int(m.group(0))
        except Exception:
            return None

    if min_v is not None and v < min_v:
        return None
    if max_v is not None and v > max_v:
        return None
    return v


def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
    else:
        s = str(value).strip()
        if not s:
            return None

        # "87%" -> 0.87
        if s.endswith("%"):
            try:
                v = float(s[:-1].strip()) / 100.0
            except Exception:
                return None
        else:
            s = s.replace(",", ".")
            try:
                v = float(s)
            except Exception:
                return None

    # normalize về 0..1 nếu OCR trả 87
    if v > 1.0:
        v = v / 100.0

    # clamp 0..1
    if v < 0.0:
        v = 0.0
    if v > 1.0:
        v = 1.0

    return v


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()

    s = str(value).strip()
    if not s:
        return None

    # chuẩn hoá vài pattern OCR hay gặp
    s = s.replace("／", "/").replace("－", "-").replace(".", "/")
    s = re.sub(r"\s+", " ", s)

    fmts = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y")
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue

    # fallback: tìm dd mm yyyy trong chuỗi (vd "ngày 25 tháng 10 năm 2025")
    m = re.search(r"(\d{1,2})\D+(\d{1,2})\D+(\d{2,4})", s)
    if m:
        d = _parse_int(m.group(1), min_v=1, max_v=31)
        mo = _parse_int(m.group(2), min_v=1, max_v=12)
        y = _parse_int(m.group(3))
        if y is not None and y < 100:
            y = 2000 + y
        if d and mo and y:
            try:
                return date(y, mo, d)
            except Exception:
                return None

    return None


def _parse_str(value: Any, *, max_len: int | None = None, allow_empty: bool = False) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s and not allow_empty:
        return None
    if max_len is not None and len(s) > max_len:
        # quá dài thì coi như invalid (theo yêu cầu: không đúng kiểu => None)
        return None
    return s


def parse_ocr_data(
    data: Optional[Union[Dict[str, Any], str]],
    ocr_key: str,
    *,
    field: FieldName,
) -> Any:
    """
    Lấy data[ocr_key] và convert theo kiểu field của model.
    Nếu không đúng kiểu/convert fail => None.
    """

    data_dict = _to_dict_if_json_str(data)
    if not isinstance(data_dict, dict):
        return None

    raw = _extract_value(data_dict.get(ocr_key))

    # map field -> type conversion theo model của bạn
    if field == "year":
        return _parse_int(raw, min_v=1900, max_v=2100)
    if field == "month":
        return _parse_int(raw, min_v=1, max_v=12)
    if field == "confidence":
        return _parse_float(raw)
    if field == "marriage_date":
        return _parse_date(raw)

    if field == "marriage_reg_no":
        # model String(100)
        return _parse_str(raw, max_len=100)

    if field == "sender":
        return _parse_str(raw, max_len=255)
    if field == "receiver":
        return _parse_str(raw, max_len=255)

    if field == "ocr_text":
        # Text: cho dài thoải mái, nhưng nếu rỗng => None
        return _parse_str(raw, allow_empty=False)

    if field == "cmnd":
        # String(20): normalize nhẹ (giữ số + chữ)
        s = _parse_str(raw, max_len=20)
        return s

    if field == "cccd":
        s = _parse_str(raw, max_len=20)
        return s
    
    if field == "document_type":
        return _parse_str(raw, max_len=255)
    
    return None