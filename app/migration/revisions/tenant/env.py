from alembic import context
from sqlalchemy import MetaData, create_engine, pool
from sqlalchemy.engine.url import URL

from logging.config import fileConfig
import app.models  # noqa: F401
from app.models.base import Base, convention
from app.config import Settings

settings = Settings()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

DRIVER = settings.mysql_driver
USER = settings.mysql_user
PASSWORD = settings.mysql_password
HOST = settings.mysql_host
PORT = settings.mysql_port
CHARSET = settings.mysql_charset


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    translated = MetaData(naming_convention=convention)

    # https://docs.sqlalchemy.org/en/14/core/metadata.html#sqlalchemy.schema.Table.to_metadata
    def translate_schema(table, to_schema, contraint, referred_schema):
        return to_schema

    for table in Base.metadata.tables.values():
        table.to_metadata(
            translated,
            schema="tenant_default" if table.schema == "tenant" else table.schema,
            referred_schema_fn=translate_schema,
        )
    schema_name = context.get_x_argument(
        as_dictionary=True).get("schema") or "tenant_default"
    url = URL.create(
        drivername=DRIVER,
        username=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        database=schema_name,
        query={"charset": CHARSET},
    )

    connectable = create_engine(
        url=url,
        poolclass=pool.NullPool,
    )

    def process_revision_directives(context, revision, directives):
        """Do not create revision files if no schema changes are detected"""
        if config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []

    def include_object(object, name, type_, reflected, compare_to):
        """Conditionally control what gets generated automatically"""
        if type_ == "table" and reflected and compare_to is None:
            return False

        elif type_ == "foreign_key_constraint":
            return False
        else:
            return True

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=translated,
            compare_type=True,
            include_schemas=True,
            include_object=include_object,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
