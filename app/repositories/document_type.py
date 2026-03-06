from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.tenant.document_type import DocumentType
from app.utils.utilities import sa_to_dict


class DocumentTypeRepository:

    def __init__(self, session: Session):
        self.session = session

    # =========================
    # GET METHODS
    # =========================

    def get_by_id(self, document_type_id: str) -> Optional[DocumentType]:
        stmt = select(DocumentType).where(
            DocumentType.id == document_type_id
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_key(self, type_key: str, version: int) -> Optional[DocumentType]:
        stmt = select(DocumentType).where(
            DocumentType.type_key == type_key,
            DocumentType.version == version,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> Optional[DocumentType]:
        stmt = (
            select(DocumentType)
            .where(DocumentType.name == name)
            .order_by(desc(DocumentType.version))
        )
        return self.session.execute(stmt).scalars().first()
    
    def all(self) -> List[DocumentType]:
        stmt = select(DocumentType)
        rows = self.session.execute(stmt).scalars().all()
        return [sa_to_dict(row) for row in rows]

    # =========================
    # INSERT
    # =========================

    def insert(self, document_type: DocumentType) -> DocumentType:
        self.session.add(document_type)
        try:
            self.session.flush()
            self.session.refresh(document_type)
            return document_type
        except IntegrityError as e:
            self.session.rollback()
            raise e

    # =========================
    # UPDATE
    # =========================

    def update(self, document_type: DocumentType) -> DocumentType:
        try:
            self.session.flush()
            self.session.refresh(document_type)
            return document_type
        except IntegrityError as e:
            self.session.rollback()
            raise e

    def deactivate(self, document_type_id: str) -> Optional[DocumentType]:
        doc_type = self.get_by_id(document_type_id)
        if not doc_type:
            return None

        doc_type.is_active = False
        return self.update(doc_type)

    # =========================
    # DELETE (optional)
    # =========================

    def delete(self, document_type: DocumentType) -> None:
        self.session.delete(document_type)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise e
