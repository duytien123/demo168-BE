from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.models.common.province import Province

from app.repositories.common.province import ProvinceRepository

from app.utils.utilities import normalize_key

from app.schemas.province import ProvinceCreate


def list_province(
    session: Session
):
    repo_province = ProvinceRepository(session)
    return repo_province.all()
 
def create_province(
    session: Session,
    body: ProvinceCreate
):
    province_key = normalize_key(body.province_name)
    repo_province = ProvinceRepository(session)

    province = repo_province.get_by_key(province_key=province_key)
    if province:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tỉnh đã tồn tại với tên {province.province_name}",
        )

    province = Province(
        province_key=province_key,
        province_name=body.province_name
    )
    repo_province.insert(province)

    session.commit()
    return province
