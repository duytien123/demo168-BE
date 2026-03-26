from typing import Any, Dict
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from starlette import status

from app.context.db.db_primary import get_db_primary_ward_teannt
from app.services import ocr as sv_ocr
from app.services import ocr_local_qwen_poc as sv_ocr_local_qwen_poc
from app.schemas.ocr import OcrLocalQwenPocResponse, OcrResponse
from app.log import logger

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post(
    path="/",
    summary="Trích xuất dữ liệu từ ảnh văn bản hành chính Việt Nam",
    tags=["OCR"],
    status_code=status.HTTP_200_OK,
    response_model=OcrResponse
)
async def ocr(
    session=Depends(get_db_primary_ward_teannt),
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    try:
       return  await sv_ocr.detect_image_text(
            session=session,
            file=file,
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("inbound: app/routers/province.py create_province", exc_info=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.post(
    path="/poc/local-qwen/",
    summary="POC OCR local DeepSeek markdown + Qwen proofread",
    tags=["OCR"],
    status_code=status.HTTP_200_OK,
    response_model=OcrLocalQwenPocResponse,
)
async def ocr_local_qwen_poc(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        return await sv_ocr_local_qwen_poc.run_local_qwen_poc(file=file)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        logger.error("inbound: app/routers/ocr.py ocr_local_qwen_poc", exc_info=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")
