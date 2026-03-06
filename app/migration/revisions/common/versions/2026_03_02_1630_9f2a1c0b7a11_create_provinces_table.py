"""create provinces table

Revision ID: 9f2a1c0b7a11
Revises:
Create Date: 2026-03-02 16:30:00.000000+07:00

"""
import sqlalchemy as sa
from alembic import op
from app.config import Settings

settings = Settings()

# revision identifiers, used by Alembic.
revision = "9f2a1c0b7a11"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_table(op.get_bind().engine, "provinces"):
        op.create_table(
            "provinces",
            sa.Column("id", sa.String(length=36), nullable=False),

            # business keys
            sa.Column("province_key", sa.String(length=20), nullable=False),
            sa.Column("province_name", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=255), nullable=True),
            sa.Column("country_code", sa.String(length=2), nullable=True),

            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),

            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),

            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),

            sa.PrimaryKeyConstraint("id", name=op.f("pk_provinces")),
            # unique
            sa.UniqueConstraint("province_key", name=op.f("uq_provinces_province_key")),
            schema=settings.common_db_name,
        )

        # Optional indexes
        if not has_index(op.get_bind().engine, "provinces", op.f("ix_provinces_province_name")):
            op.create_index(
                op.f("ix_provinces_province_name"),
                "provinces",
                ["province_name"],
                unique=False,
                schema=settings.common_db_name,
            )

        if not has_index(op.get_bind().engine, "provinces", op.f("ix_provinces_province_key")):
            op.create_index(
                op.f("ix_provinces_province_key"),
                "provinces",
                ["province_key"],
                unique=False,
                schema=settings.common_db_name,
            )


def downgrade() -> None:
    op.drop_table("provinces", schema=settings.common_db_name)
    # drop_collection("provinces", schema=settings.common_db_name)


def has_table(engine, table_name: str) -> bool:
    inspected = sa.inspect(engine)
    return inspected.has_table(table_name, schema=settings.common_db_name)


def has_index(engine, table_name: str, index_name: str) -> bool:
    inspected = sa.inspect(engine)
    indexes = inspected.get_indexes(table_name, schema=settings.common_db_name)
    for idx in indexes:
        if idx["name"] == index_name:
            return True
    return False


def has_column(engine, table_name: str, column_name: str) -> bool:
    inspected = sa.inspect(engine)
    columns = inspected.get_columns(table_name, schema=settings.common_db_name)
    for c in columns:
        if c["name"] == column_name:
            return True
    return False