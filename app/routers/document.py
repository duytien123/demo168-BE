from fastapi import APIRouter, Depends, HTTPException, Path, Body
from starlette import status

from app.log import logger

from app.context.db.db_primary import get_db_primary_ward_teannt

from app.services import document as document_service

from app.schemas.document import (
    ListDocumnentRequest,
    ListDocumnentsResponse,
    DocumentResponse,
    UpdateDocumentRequest,
    UpdateStatus
)

router = APIRouter(prefix="/document", tags=["Documents"])

@router.get(
    path="/",
    name="document",
    summary="Get documents",
    status_code=status.HTTP_200_OK,
    response_model=ListDocumnentsResponse
)
async def get_list_documents(
    session=Depends(get_db_primary_ward_teannt),
    params: ListDocumnentRequest = Depends(ListDocumnentRequest)
):
    try:
        return document_service.list_documents(
            session=session,
            params=params
        )
    except HTTPException as e:
        logger.error("app/routers/document.py get_list_documents", exc_info=str(e))
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("app/routers/document.py get_list_documents", exc_info=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    

@router.get(
    path="/{document_id}/",
    name="document",
    summary="Get document",
    status_code=status.HTTP_200_OK,
    response_model=DocumentResponse
)
async def get_document(
    session=Depends(get_db_primary_ward_teannt),
    document_id: str = Path(..., description="document id"),
):
    try:
        return document_service.get_document(
            session=session,
            document_id=document_id
        )
    except HTTPException as e:
        logger.error("app/routers/document.py get_document", exc_info=str(e))
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("app/routers/document.py get_document", exc_info=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    

@router.put(
    path="/{document_id}/",
    name="Update document",
    response_model=DocumentResponse
)
def update_document(
    document_id: str,
    params: UpdateDocumentRequest = Body(...),
    session=Depends(get_db_primary_ward_teannt),
):
    try:
        return document_service.update(
            session=session,
            document_id=document_id,
            params=params,
        )
    except HTTPException as e:
        logger.error("app/routers/document.py update_document", exc_info=str(e))
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("app/routers/document.py update_document", exc_info=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

@router.patch(
    path="/{document_id}/",
    name="Update document status",
    response_model=bool
)
def update_document_status(
    document_id: str,
    params: UpdateStatus = Body(...),
    session=Depends(get_db_primary_ward_teannt),
):
    try:
        return document_service.update_status(
            session=session,
            document_id=document_id,
            params=params
        )
    except HTTPException as e:
        logger.error("app/routers/document.py update_status", exc_info=str(e))
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("app/routers/document.py update_document", exc_info=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
