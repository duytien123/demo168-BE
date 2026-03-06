import importlib
import pkgutil
from fastapi import HTTPException
from sqlalchemy import MetaData, text, Inspector
from sqlalchemy.orm import Session
from starlette import status

from app.log import logger
from app.models.base import Base, convention
import app.models.tenant

from app.models.common.ward import Ward

from app.repositories.common.ward import WardRepository
from app.repositories.common.province import ProvinceRepository

from app.utils.utilities import normalize_key

from app.schemas.ward import WardCreate


def list_ward(
    session: Session,
    province_id: str
):
    repo_ward = WardRepository(session)
    return repo_ward.all(province_id)

 
def create_ward(
    session: Session,
    database_common: Session,
    inspector: Inspector,
    body: WardCreate
):
    repo_province = ProvinceRepository(session=database_common)
    province = repo_province.get_by_key(province_key=body.province_key)
    if not province:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tỉnh chưa tồn tại, vui lòng chọn tỉnh phù hợp!",
        )
    
    ward_key = normalize_key(body.ward_name)
    repo_ward = WardRepository(session=database_common)
    ward = repo_ward.get_by_key(
        province_id=province.id,
        ward_key=ward_key
    )
    if ward:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phường đã tồn tại, Tên trước đó: {ward.ward_name}",
        )
    database_name = body.province_key + "_" + ward_key
    if (inspector.has_schema(schema_name=database_name) and len(inspector.get_table_names(schema=database_name)) > 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phường đã tồn tại",
        )
    elif database_name not in inspector.get_schema_names():
        ward_data = Ward(
            province_id=province.id,
            ward_key=ward_key,
            ward_name=body.ward_name,
            database_name=database_name
        )
        repo_ward.insert(ward_data)

        create_schema_sql = text(f"""
            CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci
        """)
        session.execute(create_schema_sql)

    def import_all_model_modules(package):
        """
        Dynamically import all .py files inside the given package (e.g., app.models.tenant),
        except for specific files like customer.py and customer_detail.py.
        """
        imported_modules = []

        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if not is_pkg:
                full_name = f"{package.__name__}.{module_name}"
                importlib.import_module(full_name)
                imported_modules.append(full_name)

        return imported_modules

    # Import all model modules under app.models.tenant
    valid_model_modules = import_all_model_modules(app.models.tenant)

    # Create a new MetaData object and copy only the models defined under app.models.tenant
    meta = MetaData(naming_convention=convention)

    # Function to handle schema reference when copying constraints
    def referred_schema_fn(table, to_schema, constraint, referred_schema):
        return to_schema

    # Copy only the allowed models
    for table in Base.metadata.tables.values():
        model_class = next(
            (mapper.class_ for mapper in Base.registry.mappers if mapper.local_table == table),
            None
        )
        model_module = getattr(model_class, "__module__", None)

        if (model_module and any(model_module.startswith(m) for m in valid_model_modules)):
            table.to_metadata(
                meta,
                schema=database_name,
                referred_schema_fn=referred_schema_fn
            )

    # Create all selected tables in the target schema
    meta.create_all(bind=session.get_bind(), checkfirst=True)

    logger.info("Tables created:")
    for t in meta.tables.keys():
        logger.info(t)

    database_common.commit()
    session.commit()
    print("ward_data", ward_data)
    return ward_data
