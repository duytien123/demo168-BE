from fastapi import Header, HTTPException
from typing import Optional


class LocationContext:
    def __init__(self, province_key: str, ward_key: str):
        self.province_key = province_key
        self.ward_key = ward_key


def get_location_context(
    province_key: Optional[str] = Header(None, alias="x-province-key"),
    ward_key: Optional[str] = Header(None, alias="x-ward-key"),
) -> LocationContext:

    if not province_key or not ward_key:
        raise HTTPException(status_code=400, detail="Missing location headers")

    return LocationContext(province_key, ward_key)
