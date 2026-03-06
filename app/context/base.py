from enum import Enum
import hashlib
from collections import OrderedDict

from sqlalchemy import create_engine, Inspector, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from contextlib import contextmanager

from app.constants.message import Message
from app.log import logger

# cache for database engines
_engine_cache = OrderedDict()
_ENGINE_CACHE_LIMIT = 20

_shared_engines = {} 

class DatabaseType(str, Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


class SQLConfig:
    def __init__(self, host: str, port: int, username: str, password: str,  database: str,  database_type: DatabaseType = DatabaseType.MYSQL):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.drivername = database_type.value

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "database": self.database,
            "drivername": self.drivername
        }

    def to_sqlalchemy_url(self) -> str:
        return f"{self.drivername}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    

def check_connection(config: SQLConfig, timeout: int = 3) -> bool:
    """
    Check if a connection to the database can be established.
    Returns True if successful, False otherwise.
    """
    try:
        url = URL.create(**config.to_dict())
        engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": timeout}
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")) 
        logger.info(f"Database connection OK: {config.host}:{config.port}/{config.database}")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {config.host}:{config.port}/{config.database} -> {e}")
        return False


def _generate_config_hash(config: SQLConfig) -> str:
    raw = f"{config.host}|{config.port}|{config.username}|{config.password}|{config.database}|{config.drivername}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _create_engine_from_config(config: SQLConfig):
    url = URL.create(**config.to_dict())

    return create_engine(url, pool_pre_ping=True)


def get_engine(config: SQLConfig):
    """
    Automatically selects the appropriate SQLAlchemy engine:
    - If config.host already has a shared engine → reuse it (same DB host, multiple schemas).
    - If the tenant uses a separate DB host → create and cache a dedicated engine (with size limit).
    """
    host_key = f"{config.host}:{config.port}"

    # --- Case 1: Shared DB host, different schemas ---
    # Reuse the same engine for tenants on the same host to avoid multiple connection pools.
    if host_key in _shared_engines:
        engine = _shared_engines[host_key]
        return engine

    # --- Case 2: Tenant has its own DB host ---
    # Use a per-tenant engine cache with an upper limit to prevent memory leaks or pool overload.
    config_hash = _generate_config_hash(config)
    if config_hash not in _engine_cache:
        # Remove the oldest cached engine when the cache exceeds the limit.
        if len(_engine_cache) >= _ENGINE_CACHE_LIMIT:
            oldest_key, old_engine = _engine_cache.popitem(last=False)
            old_engine.dispose()
            logger.info(f"[CACHE] Removed old engine: {oldest_key}")

        _engine_cache[config_hash] = _create_engine_from_config(config)

    return _engine_cache[config_hash]


def get_inspector(config: SQLConfig) -> Inspector:
    engine = get_engine(config)
    return inspect(engine)


def get_session_maker(config: SQLConfig):
    engine = get_engine(config)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_dynamic_session(config: SQLConfig):
    session_local = get_session_maker(config)
    session = session_local()
    try:
        yield session
    except Exception as e:
        logger.error(Message.Database.CONNECT_MYSQL_ERROR, exc_info=e)
        session.rollback()
        raise e
    finally:
        session.close()
