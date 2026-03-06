from typing import List

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from starlette import status

from app.context.db.base_mysql import MySQLManager
from app.context.db.db_primary import get_base_session, get_db_primary_common

from app.schemas.ward import WardCreate, WardOut
from app.services import ward as sv_ward

from app.log import logger

router = APIRouter()



@router.get(
    path="/",
    name="Lấy danh sách phường",
    summary="lấy danh sách Phường",
    status_code=status.HTTP_200_OK,
    response_model=List[WardOut]
)
async def get_list_province(
    province_id: str = Query(None),
    session_common=Depends(get_db_primary_common),
):
    try:
        return sv_ward.list_ward(
            session=session_common,
            province_id=province_id
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
    summary="Đăng ký phường mới",
    tags=["wards"],
    status_code=status.HTTP_200_OK,
    response_model=WardOut
)
async def create_ward(
    session: Session = Depends(get_base_session),
    database_common=Depends(get_db_primary_common),
    sql_manager=Depends(MySQLManager.Instance),
    form_data: WardCreate =  Body(...),
):
    try:
        inspector = sql_manager.get_inspect()
        return sv_ward.create_ward(
            session=session,
            database_common=database_common,
            inspector=inspector,
            body=form_data,
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("inbound: app/routers/ward.py create_ward", exc_info=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")
