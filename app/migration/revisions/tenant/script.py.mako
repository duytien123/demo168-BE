"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
from app.migrations.for_each_schema import for_each_schema
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

@for_each_schema
def upgrade(schema: str) -> None:
    ${upgrades if upgrades else "pass"}


@for_each_schema
def downgrade(schema: str) -> None:
    ${downgrades if downgrades else "pass"}


def has_table(engine, table_name: str, schema: str) -> bool:
    """テーブルが存在するかチェックする."""
    inspected = sa.inspect(engine)
    has = inspected.has_table(table_name, schema)
    return has


def has_index(engine, table_name: str, index_name: str, schema: str) -> bool:
    """インデックスが存在するかチェックする."""
    inspected = sa.inspect(engine)
    indexes = inspected.get_indexes(table_name, schema)
    has: bool = False
    for idx in indexes:
        if idx["name"] == index_name:
            has = True
            break
    return has


def has_column(engine, table_name: str, column_name: str, schema: str) -> bool:
    """カラムが存在するかチェックする."""
    inspected = sa.inspect(engine)
    columns = inspected.get_columns(table_name, schema)
    has: bool = False
    for c in columns:
        if c["name"] == column_name:
            has = True
            break
    return has