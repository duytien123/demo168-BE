from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.utils.utilities import sa_to_dict, make_data_url, merge_document

from app.repositories.document import DocumentRepository
from app.repositories.document_file import DocumentFileRepository
from app.repositories.document_type import DocumentTypeRepository
from app.repositories.document_file import DocumentFileRepository

from app.schemas.document import ListDocumnentRequest, UpdateDocumentRequest, UpdateStatus


def get_document(
    session: Session,
    document_id: str
):
    repo_document = DocumentRepository(session)
    doc = repo_document.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    repo_document_file = DocumentFileRepository(session)
    doc_file = repo_document_file.get_by_document_id(doc.id)

    repo_document_type = DocumentTypeRepository(session)
    old_document_type = repo_document_type.get_by_id(doc.document_type_id)
    document_type_name = None
    if old_document_type:
        document_type_name = old_document_type.name
    
    return  { 
        **sa_to_dict(doc),
        "document_type_name": document_type_name,
        "image_base64": make_data_url(doc_file.image_base64, doc_file.image_content_type)
    }
 
def list_documents(
    session: Session,
    params: ListDocumnentRequest
):
    repo_document = DocumentRepository(session)
    return repo_document.search_documents(
        keyword=params.keyword,
        document_type_id=params.document_type_id,
        status=params.status,
        order_by=params.order_by,
        limit=params.limit,
        offset=params.offset
    )

def update(
    session: Session,
    document_id: str,
    params: UpdateDocumentRequest,
):
    repo_document = DocumentRepository(session)
    document = repo_document.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=400, detail="Tài liệu khống tồn tại")
    
    repo_document_type = DocumentTypeRepository(session)
    old_document_type = repo_document_type.get_by_id(params.document_type_id)
    if not old_document_type:
        raise HTTPException(status_code=400, detail="Loại tài liệu khống tồn tại")
    
    # merge
    document = merge_document(document, params, ignore_none=True)
    document.status = "SUCCESS"
    document.confidence = 1
    document.version_no += 1
    # update (flush + refresh)
    repo_document.update(document)

    # commit tại service layer
    session.commit()
    session.refresh(document)

    return sa_to_dict(document)
    

def update_status(
    session: Session,
    document_id: str,
    params: UpdateStatus,
):
    repo_document = DocumentRepository(session)
    if not repo_document.update_status(document_id, params.status):
        raise HTTPException(status_code=400, detail="Tài liệu khống tồn tại")

    # commit tại service layer
    session.commit()
    return True
