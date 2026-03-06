from fastapi import APIRouter
from app.routers.ocr import router as router_ocr
from app.routers.document import router as router_document
from app.routers.document_type import router as router_document_type


router = APIRouter()

router.include_router(router=router_ocr, tags=["OCR"])
router.include_router(router=router_document, tags=["Documents"])
router.include_router(router=router_document_type, tags=["Document type"])
