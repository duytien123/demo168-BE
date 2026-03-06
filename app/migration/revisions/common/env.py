from logging.config import fileConfig

import app.models.common  # noqa: F401
from alembic import context
from app.models.common.base import BaseModel
from sqlalchemy import create_engine, pool
from sqlalchemy.engine.url import URL

from app.config import Settings

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
target_metadata = BaseModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

settings = Settings()
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

    url = URL.create(
        drivername=DRIVER,
        username=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        database=settings.common_db_name,
        query={"charset": CHARSET},
    )

    connectable = create_engine(
        url=url,
        poolclass=pool.NullPool,
    )

    def process_revision_directives(context, revision, directives):
        if config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
