"""create wards table

Revision ID: 6621c8ef4f69
Revises: 9f2a1c0b7a11
Create Date: 2026-03-02 16:31:00.000000+07:00

"""
import sqlalchemy as sa
from alembic import op
# from migration.mongodb.migrate_collection import create_collection, drop_collection
from app.config import Settings

settings = Settings()

# revision identifiers, used by Alembic.
revision = "6621c8ef4f69"
down_revision = "9f2a1c0b7a11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_table(op.get_bind().engine, "wards"):
        op.create_table(
            "wards",
            sa.Column("id", sa.String(length=36), nullable=False),

            # tenant / db scope
            sa.Column("database_name", sa.String(length=64), nullable=False),

            # link to province
            sa.Column("province_id", sa.String(length=36), nullable=False),

            # ward fields
            sa.Column("ward_key", sa.String(length=20), nullable=False),
            sa.Column("ward_name", sa.String(length=255), nullable=True),
            sa.Column("slug", sa.String(length=255), nullable=True),

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

            sa.PrimaryKeyConstraint("id", name=op.f("pk_wards")),

            # unique ward id inside tenant scope
            sa.UniqueConstraint("database_name", "ward_key", name=op.f("uq_wards_database_name_ward_key")),

            # FK: (id) -> provinces(id)
            sa.ForeignKeyConstraint(
                ["province_id"],
                [f"{settings.common_db_name}.provinces.id"],
                name=op.f("fk_wards_provinces"),
                ondelete="CASCADE",
            ),
            schema=settings.common_db_name,
        )

        # Optional indexes
        if not has_index(op.get_bind().engine, "wards", op.f("ix_wards_province_id")):
            op.create_index(
                op.f("ix_wards_province_id"),
                "wards",
                ["province_id"],
                unique=False,
                schema=settings.common_db_name,
            )

        if not has_index(op.get_bind().engine, "wards", op.f("ix_wards_ward_name")):
            op.create_index(
                op.f("ix_wards_ward_name"),
                "wards",
                ["ward_name"],
                unique=False,
                schema=settings.common_db_name,
            )

        # create_collection(
        #     "wards",
        #     ix_key_list=["database_name"],
        #     schema=settings.common_db_name,
        # )


def downgrade() -> None:
    op.drop_table("wards", schema=settings.common_db_name)
    # drop_collection("wards", schema=settings.common_db_name)


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