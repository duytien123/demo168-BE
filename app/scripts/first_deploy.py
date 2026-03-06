from typing import Final

from sqlalchemy import create_engine, pool, text
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.log import logger

settings = Settings()
MYSQL_DRIVER = settings.mysql_driver
MYSQL_USER = settings.mysql_user
MYSQL_PASSWORD = settings.mysql_password
MYSQL_HOST = settings.mysql_host
MYSQL_PORT = settings.mysql_port
MYSQL_CHARSET = settings.mysql_charset

url = URL.create(
    drivername=MYSQL_DRIVER,
    username=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    query={"charset": MYSQL_CHARSET},
)

engine = create_engine(
    url=url,
    poolclass=pool.NullPool,
)

Session = sessionmaker(engine)

CHARA_SET: Final = "utf8mb4"
COLLATE: Final = "utf8mb4_0900_ai_ci"
SCHEMAS: Final = ["common", "tenant_default"]


def setup():
    """Scripts that are only valid the first time they are deployed"""
    try:
        with Session.begin() as session:
            for schema in SCHEMAS:
                create_schema = text(
                    f"CREATE DATABASE IF NOT EXISTS {schema} CHARACTER SET {CHARA_SET} COLLATE {COLLATE}"
                )
                session.execute(create_schema)
        logger.info("Suucess to create schemas. 'common', 'tenant_default'")
    except Exception as e:
        session.rollback()
        logger.error("Failed to create schemas. 'common', 'tenant_default'", exc_info=e)


if __name__ == "__main__":
    setup()
