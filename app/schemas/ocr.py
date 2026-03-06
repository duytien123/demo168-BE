from pydantic import BaseModel
from typing import Any, Optional, Dict

class OcrResponse(BaseModel):
    data: Dict[str, Any]
