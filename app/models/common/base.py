from sqlalchemy import MetaData
from sqlalchemy.orm import as_declarative

from app.models.base import convention, MixinBaseModel

_metadata_obj = MetaData(schema="common", naming_convention=convention)


@as_declarative(metadata=_metadata_obj)
class BaseModel(MixinBaseModel):
    ...
