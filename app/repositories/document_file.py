from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.tenant.document_field import DocumentField

class DocumentFileRepository:

    def __init__(self, session: Session):
        self.session = session

    # =========================
    # GET METHODS
    # =========================

    def get_by_document_id(self, document_id: str) -> Optional[DocumentField]:
        stmt = select(DocumentField).where(
            DocumentField.document_id == document_id
        )
        return self.session.execute(stmt).scalar_one_or_none()


    def insert(self, document_type: DocumentField) -> DocumentField:
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

    def update(self, document_type: DocumentField) -> DocumentField:
        try:
            self.session.flush()
            self.session.refresh(document_type)
            return document_type
        except IntegrityError as e:
            self.session.rollback()
            raise e

    # =========================
    # DELETE (optional)
    # =========================

    def delete(self, document_type: DocumentField) -> None:
        self.session.delete(document_type)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise e
