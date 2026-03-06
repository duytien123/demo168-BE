from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.common.ward import Ward

from app.utils.utilities import sa_to_dict


class WardRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_key(self, province_id: str, ward_key: str) -> Optional[Ward]:
        stmt = select(Ward).where(
            Ward.province_id == province_id,
            Ward.ward_key == ward_key,
        )
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_first(self) -> Optional[Ward]:
        stmt = select(Ward)

        return self.session.execute(stmt).scalars().first()
    
    def all(self, province_id: str = None) -> List[Ward]:
        stmt = select(Ward)
        if province_id:
            stmt = stmt.where(
                Ward.province_id == province_id
            )
        rows = self.session.execute(stmt).scalars().all()
        return [sa_to_dict(row) for row in rows]

    def insert(self, ward: Ward) -> Ward:
        """
        Insert 1 row.
        - commit + refresh để trả object đầy đủ (id, timestamps...)
        - rollback nếu lỗi
        """
        self.session.add(ward)
        try:
            self.session.flush()
            self.session.refresh(ward)
            return ward
        except IntegrityError as e:
            self.session.rollback()
            raise e
