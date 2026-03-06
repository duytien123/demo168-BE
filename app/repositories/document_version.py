from __future__ import annotations

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.tenant.document_version import DocumentVersion


class DocumentVersionRepository:

    def __init__(self, session: Session):
        self.session = session

    # ===============================
    # GET METHODS
    # ===============================

    def get_by_document_id(self, document_id: str) -> Optional[DocumentVersion]:
        stmt = select(DocumentVersion).where(DocumentVersion.document_id == document_id)
        return self.session.execute(stmt).scalar_one_or_none()
    
    # ===============================
    # INSERT
    # ===============================

    def insert(self, document_version: DocumentVersion) -> DocumentVersion:
        self.session.add(DocumentVersion)
        try:
            self.session.flush()
            self.session.refresh(document_version)
            return document_version
        except IntegrityError as e:
            self.session.rollback()
            raise e


    # ===============================
    # VERSION SUPPORT
    # ===============================

    def get_latest_version(self, document_id: str) -> Optional[int]:
        stmt = select(func.max(DocumentVersion.version_no)).where(
            DocumentVersion.document_id == document_id
        )
        max_version = self.session.execute(stmt).scalar()
        return max_version or 0
