from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.log import logger

from app.context.db.db_primary import get_db_primary_ward_teannt

from app.services import document_type as document_type_service

from app.schemas.document_type import DocumentTypeBase

router = APIRouter(prefix="/document_type", tags=["Document type"])

@router.get(
    path="/",
    name="document_type",
    summary="Get document types",
    status_code=status.HTTP_200_OK,
    response_model=List[DocumentTypeBase]
)
async def get_list_document_type(
    session=Depends(get_db_primary_ward_teannt),
):
    try:
        return document_type_service.list_document_types(
            session=session
        )
    except HTTPException as e:
        logger.error("app/routers/document_type.py list_document_types", exc_info=str(e))
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("app/routers/document_type.py list_document_types", exc_info=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )