from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.common.province import Province
from app.utils.utilities import sa_to_dict


class ProvinceRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_key(self, province_key: str) -> Optional[Province]:
        stmt = select(Province).where(
            Province.province_key == province_key
        )
        return self.session.execute(stmt).scalar_one_or_none()
    
    def all(self) -> List[Province]:
        stmt = select(Province)
        rows = self.session.execute(stmt).scalars().all()
        return [sa_to_dict(row) for row in rows]

    def insert(self, province: Province) -> Province:
        """
        Insert 1 row.
        - commit + refresh để trả object đầy đủ (id, timestamps...)
        - rollback nếu lỗi
        """
        self.session.add(province)
        try:
            self.session.flush()
            self.session.refresh(province)
            return province
        except IntegrityError as e:
            self.session.rollback()
            raise e
