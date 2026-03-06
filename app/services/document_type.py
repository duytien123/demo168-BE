from sqlalchemy.orm import Session

from app.repositories.document_type import DocumentTypeRepository
 
def list_document_types(
    session: Session,
):
    repo_document_type = DocumentTypeRepository(session)
    return repo_document_type.all()
