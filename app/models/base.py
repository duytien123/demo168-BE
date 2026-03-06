from sqlalchemy import MetaData, Column, Integer, DateTime, Table, inspect
from sqlalchemy.orm import Session, registry, as_declarative

from datetime import datetime


# ==== CONFIG ====
TENANT_BASE_TTL = 600      # TTL 10 minutes for each tenant's Base
TENANT_BASE_MAXSIZE = 200   # Maximum 200 tenants in the cache
MODEL_CACHE_TTL = 600       # TTL 10 minutes for dynamic model cache
MODEL_CACHE_MAXSIZE = 200   # Maximum 200 tables per tenant


mapper_registry = registry()

convention = {
    "ix": "ix_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class MixinBaseModel:
    def as_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.attrs}
    


metadata_obj = MetaData(schema="tenant", naming_convention=convention)


@as_declarative(metadata=metadata_obj)
class Base(MixinBaseModel):
    ...

    def delete(self, session: Session):
        session.delete(self)

    def delete_with_flush(self, session: Session):
        self.delete(session)
        session.flush()


class BaseModel:
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    del_flg = Column(Integer, nullable=False, default=0, server_default="0")

