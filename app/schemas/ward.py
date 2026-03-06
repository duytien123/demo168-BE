from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WardBase(BaseModel):
    database_name: str = Field(..., max_length=64)
    province_id: str = Field(..., max_length=36)

    ward_key: str = Field(..., max_length=20)
    ward_name: Optional[str] = Field(default=None, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)

    is_active: bool = True


class WardUpdate(BaseModel):
    # update thường cho phép optional
    province_id: Optional[str] = Field(default=None, max_length=20)
    ward_name: Optional[str] = Field(default=None, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class WardOut(WardBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class WardCreate(BaseModel):
    province_key: str = Field(..., max_length=255, example="dak_lak")
    ward_name: str = Field(..., max_length=255, example="Phường 11")