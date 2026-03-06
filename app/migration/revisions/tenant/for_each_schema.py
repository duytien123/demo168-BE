from functools import wraps

from alembic import op
from sqlalchemy import inspect
from app.log import logger


def for_each_schema(fn_migration):
    @wraps(fn_migration)
    def wrapper():
        schema_lsit = (
            op.get_bind().execute("SELECT database_name FROM common.tenant").fetchall()
        )
        inspect_result = inspect(op.get_bind().engine)
        schema_names = inspect_result.get_schema_names()
        if len(schema_lsit) != 0:
            migrated_schemas = []
            not_created_schemas = []
            for (schema,) in schema_lsit:
                if schema in schema_names:
                    fn_migration(schema)
                    migrated_schemas.append(schema)
                else:
                    not_created_schemas.append(schema)

            count_exists_schema = len(schema_lsit)
            count_migrated_schema = len(migrated_schemas)
            count_not_migrated_schema = len(not_created_schemas)
            count_detected_schmea = count_migrated_schema + count_not_migrated_schema

            migrated_schema_names = ",".join(migrated_schemas)
            not_migrated_schema_names = ",".join(not_created_schemas)

            logger.info(
                f"Total Schemas: {count_exists_schema}"
                f"\nMigration target: {count_migrated_schema}"
                f"\nUncreated Schema: {count_not_migrated_schema}"
                f"\nMigration target + Uncreated schema"
                f"\n = {count_detected_schmea}(Number of schemas discovered)"
                f"\n{count_detected_schmea}(Number of schemas discovered)/{count_exists_schema}(Total Schemas)"
                f"\nList of schemas to be migrated"
                f"\n{migrated_schema_names}"
                f"\nList of uncreated schemas"
                f"\n{not_migrated_schema_names}"
            )

    return wrapper
