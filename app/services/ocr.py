from fastapi import HTTPException
from sqlalchemy.orm import Session
import base64

from app.models.tenant.document import Document as DocumentModel
from app.models.tenant.document_type import DocumentType as DocumentTypeModel
from app.models.tenant.document_field import DocumentField as DocumentFieldModel

from app.externals import ocr_api
from app.constants.prompt import OcrDefault, OCR_MODEL

from app.repositories.document import DocumentRepository
from app.repositories.document_type import DocumentTypeRepository
from app.repositories.document_file import DocumentFileRepository

from app.utils.utilities import to_dict, normalize_key
from app.utils.ocr import parse_ocr_data


async def detect_image_text(
    session: Session,
    file
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    
    image_base64 = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "model": OCR_MODEL,
        "system": OcrDefault.SYSTEM.strip(),
        "prompt": OcrDefault.PROMPT_TEMPLATE.strip(),
        "stream": False,
        "images": [image_base64],
        "format": "json"
    }

    response = ocr_api.call(
        method="POST",
        json=payload
    )
    data = None
    if response["status"] == 200:
        data = response["data"].json()
        data_dict = to_dict(data)
    else:
        raise HTTPException(status_code=400, detail="Không thể trích xuất dữ liệu từ ảnh văn bản hành chính, vui lòng thửu lại!")

    thinking = to_dict(data_dict.get("thinking"))
    if not thinking or not thinking.get("fixed"):
        raise HTTPException(status_code=400, detail="Không thể trích xuất dữ liệu từ ảnh văn bản hành chính, vui lòng thửu lại!")

    data_fixed_key = to_dict(thinking.get("fixed"))
    
    document_type_name = parse_ocr_data(data_fixed_key, "loai_tai_lieu", field="document_type")
    if not document_type_name:
        document_type_name = "Loại tài liệu chưa xác định"

    repo_document_type = DocumentTypeRepository(session)
    old_document_type = repo_document_type.get_by_name(document_type_name)
    if old_document_type:
        document_type_id = old_document_type.id
        type_key = old_document_type.type_key
    else:
        type_key = normalize_key(document_type_name)
        new_data = DocumentTypeModel(
            name=document_type_name,
            type_key=type_key
        )
        new_document_type = repo_document_type.insert(new_data)
        document_type_id = new_document_type.id

    repo_document = DocumentRepository(session)

    marriage_date   = parse_ocr_data(data_fixed_key, "ngay_tao", field="marriage_date")
    marriage_reg_no = parse_ocr_data(data_fixed_key, "so_ky_hieu", field="marriage_reg_no")
    year            = parse_ocr_data(data_fixed_key, "year", field="year")
    month           = parse_ocr_data(data_fixed_key, "month", field="month")
    sender          = parse_ocr_data(data_fixed_key, "sender", field="sender")
    receiver        = parse_ocr_data(data_fixed_key, "receiver", field="receiver")
    ocr_text        = parse_ocr_data(data_fixed_key, "noi_dung_chinh", field="ocr_text")
    confidence      = parse_ocr_data(data_fixed_key, "confidence", field="confidence")
    cmnd            = parse_ocr_data(data_fixed_key, "cmnd", field="cmnd")
    cccd            = parse_ocr_data(data_fixed_key, "cccd", field="cccd")

    if marriage_reg_no:
        if repo_document.get_by_marriage_reg_no(marriage_reg_no):
            raise HTTPException(status_code=400, detail="Tài liệu đã được tạo trước đó")

    new_document_data = DocumentModel(
        document_type_id=document_type_id,
        marriage_date=marriage_date,
        year=year,
        month=month,
        marriage_reg_no=marriage_reg_no,
        sender=sender,
        receiver=receiver,
        version_no=1,
        file_uri_original=file.filename,
        file_uri_processed=None,
        ocr_text=ocr_text,
        ocr_json=data_fixed_key,
        confidence=confidence,
        cmnd=cmnd,
        cccd=cccd
    )
    repo_document.insert(new_document_data)

    repo_document_file = DocumentFileRepository(session)
    new_data_file = DocumentFieldModel(
        document_id=new_document_data.id,
        field_key=file.filename,
        image_base64=image_base64,
        image_content_type=(file.content_type or "application/octet-stream")
    )
    repo_document_file.insert(new_data_file)

    session.commit()

    return {"data": thinking}
