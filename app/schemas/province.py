from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ProvinceBase(BaseModel):
    province_key: str
    province_name: str
    slug: Optional[str] = None
    country_code: Optional[str] = None
    is_active: bool = True

class ProvinceOut(ProvinceBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ProvinceCreate(BaseModel):
    province_name: str = Field(..., max_length=255, example="Đắk Lắk")
