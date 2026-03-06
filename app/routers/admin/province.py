from typing import List

from fastapi import APIRouter, Depends, HTTPException, Body
from starlette import status

from app.context.db.db_primary import get_db_primary_common

from app.schemas.province import ProvinceCreate, ProvinceOut
from app.services import province as sv_province

from app.log import logger

router = APIRouter()


@router.get(
    path="/",
    name="Get all",
    summary="lấy danh sách tỉnh",
    status_code=status.HTTP_200_OK,
    response_model=List[ProvinceOut]
)
async def get_list_province(
    session_common=Depends(get_db_primary_common),
):
    try:
        return sv_province.list_province(
            session=session_common
        )
    except HTTPException as e:
        logger.error("app/routers/province.py list_province", exc_info=str(e))
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("app/routers/province.py list_province", exc_info=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

@router.post(
    path="/",
    summary="Đăng ký đơn vị tỉnh",
    tags=["provinces"],
    status_code=status.HTTP_200_OK,
    response_model=ProvinceOut
)
async def create_province(
    session=Depends(get_db_primary_common),
    form_data: ProvinceCreate =  Body(...),
):
    try:
       return sv_province.create_province(
            session=session,
            body=form_data,
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("inbound: app/routers/province.py create_province", exc_info=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")
