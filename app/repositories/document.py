from __future__ import annotations

from typing import Optional, List
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.tenant.document import Document
from app.models.tenant.document_type import DocumentType
from app.utils.query_helper import retrieve_sort_columns_orm
from app.utils.utilities import sa_to_dict


class DocumentRepository:

    def __init__(self, session: Session):
        self.session = session

    # ===============================
    # GET METHODS
    # ===============================

    def get_by_id(self, document_id: str) -> Optional[Document]:
        stmt = select(Document).where(Document.id == document_id)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_by_marriage_reg_no(self, marriage_reg_no: str) -> Optional[Document]:
        stmt = select(Document).where(Document.marriage_reg_no == marriage_reg_no)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_cccd(self, cccd: str) -> List[Document]:
        stmt = select(Document).where(Document.cccd == cccd)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_cmnd(self, cmnd: str) -> List[Document]:
        stmt = select(Document).where(Document.cmnd == cmnd)
        return list(self.session.execute(stmt).scalars().all())

    def filter_by_year_month(
        self,
        document_type_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> List[Document]:

        conditions = [Document.document_type_id == document_type_id]

        if year is not None:
            conditions.append(Document.year == year)

        if month is not None:
            conditions.append(Document.month == month)

        stmt = select(Document).where(and_(*conditions))

        return list(self.session.execute(stmt).scalars().all())

    # ===============================
    # INSERT
    # ===============================

    def insert(self, document: Document) -> Document:
        self.session.add(document)
        try:
            self.session.flush()
            self.session.refresh(document)
            return document
        except IntegrityError as e:
            self.session.rollback()
            raise e

    # ===============================
    # UPDATE
    # ===============================

    def update(self, document: Document) -> Document:
        try:
            self.session.flush()
            self.session.refresh(document)
            return document
        except IntegrityError as e:
            self.session.rollback()
            raise e

    def update_status(self, document_id: str, status: str) -> Optional[Document]:
        print("document_id", document_id)
        doc = self.get_by_id(document_id)
        if not doc:
            return None

        if status == "SUCCESS":
            doc.confidence = 1

        doc.status = status
        return self.update(doc)

    # ===============================
    # DELETE
    # ===============================

    def delete(self, document: Document) -> None:
        self.session.delete(document)
        try:
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise e

    # ===============================
    # SEARCH (basic)
    # ===============================

    def search_by_keyword(self, keyword: str) -> List[Document]:
        stmt = select(Document).where(
            Document.ocr_text.ilike(f"%{keyword}%")
        )
        return list(self.session.execute(stmt).scalars().all())
    

    def search_documents(
        self,
        keyword: Optional[str] = None,
        document_type_id: Optional[str] = None,
        status: Optional[str] = None,
        order_by: str = "-created_at",
        limit: int = 50,
        offset: int = 0,
    ) -> List[Document]:

        base_stmt = (
            select(Document, DocumentType.name.label("document_type_name"))
            .join(
                DocumentType,
                Document.document_type_id == DocumentType.id,
                isouter=True,  # LEFT JOIN
            )
        )

        conditions = []
        if keyword:
            conditions.append(Document.ocr_text.ilike(f"%{keyword}%"))
        if document_type_id:
            conditions.append(Document.document_type_id == document_type_id)
        if status:
            conditions.append(Document.status == status)

        if conditions:
            base_stmt = base_stmt.where(and_(*conditions))

        # ORDER BY
        sort_columns = retrieve_sort_columns_orm(order_by, Document)
        if sort_columns:
            base_stmt = base_stmt.order_by(*sort_columns)

        # ✅ COUNT(*) query (đếm theo Document.id để tránh join làm phình)
        count_stmt = (
            select(func.count(func.distinct(Document.id)))
            .select_from(Document)
            .join(
                DocumentType,
                Document.document_type_id == DocumentType.id,
                isouter=True,
            )
        )
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))

        total_count = self.session.execute(count_stmt).scalar_one()
        total_pages = (total_count // limit) + (1 if total_count % limit > 0 else 0)

        # paging
        page_stmt = base_stmt.limit(limit).offset(offset)

        rows = self.session.execute(page_stmt).all()
        data = [
            {
                **sa_to_dict(row[0]),              # Document -> dict
                "document_type_name": row[1],      # joined column
            }
            for row in rows
        ]

        return {
            "data": data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "total_pages": total_pages,
        }

    # ===============================
    # VERSION SUPPORT
    # ===============================

    def get_latest_version(self, document_id: str) -> Optional[int]:
        doc = self.get_by_id(document_id)
        if not doc:
            return None
        return doc.version_no
