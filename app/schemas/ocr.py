from pydantic import BaseModel, Field
from typing import Any, Dict, List

class OcrResponse(BaseModel):
    data: Dict[str, Any]


class OcrLocalQwenPocResponse(BaseModel):
    provider: str = "local_deepseek_qwen"
    file_name: str
    mime_type: str
    pages_processed: int = 1
    markdown_raw: str = ""
    markdown_corrected: str = ""
    extracted: Dict[str, Any] = Field(default_factory=dict)
    export_file_name: str = ""
    export_content_type: str = "application/msword"
    export_base64: str = ""
    warnings: List[str] = Field(default_factory=list)
