from pydantic import BaseModel, Field

class DocumentTypeBase(BaseModel):
    id: str = Field(...)
    name: str = Field(...)
