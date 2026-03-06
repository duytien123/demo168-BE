import threading
from cachetools import TTLCache
from typing import Optional, Mapping

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool
from starlette_context import context
from contextvars import ContextVar

from app.constants.enum import SchemaType
from app.utils.singleton import Singleton
from app.config import Settings

settings = Settings()


# --- MySQL Connection Config ---
DRIVER = settings.mysql_driver
USER = settings.mysql_user
PASSWORD = settings.mysql_password
HOST = settings.mysql_host
PORT = settings.mysql_port
CHARSET = settings.mysql_charset
POOL_RECYCLE = settings.sqlalchemy_pool_recycle
SCHEMA_COMMON = settings.common_db_name
DB_POOL_SIZE = settings.db_pool_size
DB_MAX_OVERFLOW = settings.db_max_overflow
DB_POOL_TIMEOUT = settings.db_pool_timeout

# --- Global Context ---
context: ContextVar = ContextVar("context", default={})

# --- Global Engine Cache (Max 50 engines, TTL = 30min) ---
_ENGINE_CACHE = TTLCache(maxsize=50, ttl=1800)


# --- Engine Cache Helper ---
def setup_engine_cache(url: URL):
    """
    Create or reuse a cached SQLAlchemy engine based on HOST:PORT.
    This prevents memory leaks when spamming connection creation.
    """
    cache_key = f"{USER}@{HOST}:{PORT}"

    # Reuse existing engine if cached
    if cache_key in _ENGINE_CACHE:
        return _ENGINE_CACHE[cache_key]

    # Use QueuePool to limit and reuse connections
    engine = create_engine(
        url=url,
        echo=False,
        poolclass=QueuePool,
        pool_size=DB_POOL_SIZE,                 # Maximum number of persistent connections in the pool
        max_overflow=DB_MAX_OVERFLOW,           # Maximum number of temporary connections beyond pool_size
        pool_recycle=POOL_RECYCLE,              # Recycle (refresh) connections periodically (minutes)
        pool_timeout=DB_POOL_TIMEOUT,           # Maximum time (in seconds) to wait for an available connection before timing out
        pool_pre_ping=True,                     # Validate connection before using it (detects dropped connections)
        connect_args={"connect_timeout": 10},   # Timeout for establishing a new connection
    )
    _ENGINE_CACHE[cache_key] = engine

    # Add cleanup logic (optional)
    if not hasattr(_ENGINE_CACHE, "_engine_cleanup"):
        def cleanup_engines():
            """Remove and dispose expired or stale engines."""
            removed = []
            for key in list(_ENGINE_CACHE.keys()):
                engine = _ENGINE_CACHE.get(key)
                if engine and getattr(engine, "pool", None) is None:
                    removed.append(key)
                    del _ENGINE_CACHE[key]
            if removed:
                print(f"[ENGINE CACHE CLEANUP] Removed stale engines: {removed}")

        _ENGINE_CACHE._engine_cleanup = cleanup_engines

    return engine


# --- Base Class (shared between MySQLManager and MySQLManagerOB) ---
class BaseMySQLManager:
    def __init__(self, use_scopefunc: bool = True):
        # Define safe scopefunc
        def safe_scopefunc():
            try:
                if isinstance(context, dict):
                    return context.get("request_id")
                ctx_val = context.get({})
                return ctx_val.get("request_id") if isinstance(ctx_val, dict) else None
            except Exception:
                return threading.get_ident()

        self.session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False),
            scopefunc=safe_scopefunc if use_scopefunc else None,
        )

        # Build connection URL
        self.url = URL.create(
            drivername=DRIVER,
            username=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            query={"charset": CHARSET},
        )

        # self._base_engine = create_engine(url=self.url, echo=True, poolclass=NullPool)
        # Reuse cached engine
        self._base_engine = setup_engine_cache(self.url)

    # --- Session Creation Helpers ---
    def _get_session(self, schema_translate_map: dict):
        """Create a new independent session for each schema map."""
        schema_engine = self._base_engine.execution_options(
            schema_translate_map=schema_translate_map
        )
        SessionLocal = sessionmaker(bind=schema_engine, autocommit=False, autoflush=False)
        return SessionLocal()
    
    def get_session_all(self):
        """Return a global scoped session bound to the base engine."""
        if not hasattr(self, "_base_engine") or self._base_engine is None:
            raise RuntimeError("Base engine not initialized")
        return self.session(bind=self._base_engine)

    def map_schema(self, schema_translate_map: Optional[Mapping[Optional[str], Optional[str]]]):
        return self._get_session(schema_translate_map)

    def get_session(self, schema: str, schema_type: str):
        return self._get_session({None: schema, f"{schema_type}": schema})

    def get_base_session(self, init_ob_schema: str, include_common_schema: bool = False, schemas: dict = None):
        """
        Creates a SQLAlchemy session with configurable schema mappings for database operations.

        This function allows flexible configuration of database schema mappings, supporting multiple schemas
        including outbound, common, and custom schemas. It's particularly useful when operations need to
        span across different database schemas.

        Args:
            init_ob_schema (str): The initial outbound schema name to be used as the default schema.
            include_common_schema (bool, optional): Whether to include the common schema in the mapping. Defaults to False.
            schemas (dict, optional): Additional schema mappings where keys are schema types from SchemaType enum
                                    and values are schema names. Defaults to None.

        Returns:
            Session: A SQLAlchemy session configured with the specified schema mappings.

        Example:
            # Basic usage with just outbound schema
            session = get_base_session("tenant_ob")
            
            # Including common schema
            session = get_base_session("tenant_ob", include_common_schema=True)
            
            # With additional custom schemas
            custom_schemas = {SchemaType.TENANT.value: "custom_schema"}
            session = get_base_session("tenant_ob", schemas=custom_schemas)
        """
        schema_translate_map = {
            None: init_ob_schema,
            SchemaType.TENANT.value: init_ob_schema
        }

        if include_common_schema:
            schema_translate_map[SchemaType.COMMON.value] = SCHEMA_COMMON

        if schemas and isinstance(schemas, dict):
            schema_translate_map.update(schemas)

        return self._get_session(schema_translate_map)

    def get_tenant_session(self, schema_tenant: str):
        """
        Creates a SQLAlchemy session that maps both outbound and inbound schemas for a tenant.

        This function creates a session that can work with both outbound and inbound schemas
        for a tenant, along with the common schema. It's specifically designed for operations
        that need to access both outbound and inbound data for a tenant.

        Args:
            schema_tenant (str): The schema name for the tenant.

        Returns:
            Session: A SQLAlchemy session configured to work with both outbound and inbound schemas,
                    plus the common schema. The session maps:
                    - None and SchemaType.TENANT.value to schema_tenant
                    - SchemaType.COMMON.value to common schema

        Example:
            # Create a session for a tenant with both outbound and inbound schemas
            session = get_tenant_session("tenant_ob", "tenant_ib")
        """
        schema_translate_map = {
            None: schema_tenant,
            SchemaType.TENANT.value: schema_tenant,
            SchemaType.COMMON.value: SCHEMA_COMMON
        }

        return self._get_session(schema_translate_map)

    def independ_schema_session(self, schema: str, schema_type: str):
        """Return a standalone session factory (not thread-local)."""
        schema_engine = self._base_engine.execution_options(
            schema_translate_map={None: schema, f"{schema_type}": schema}
        )
        return sessionmaker(bind=schema_engine, autocommit=False, autoflush=False)

    def get_session_with_schema(self, schema: str, schema_type: str):
        """Thread Local なセッションを return する"""
        return self._get_session({None: schema, f"{schema_type}": schema})

    def remove(self):
        """Remove thread-local session."""
        self.session.remove()

    def get_inspect(self):
        return inspect(self._base_engine)


# --- MySQLManager (General Use) ---
@Singleton
class MySQLManager(BaseMySQLManager):
    def __init__(self):
        super().__init__(use_scopefunc=True)


# --- MySQLManagerOB (Outbound-Specific) ---
@Singleton
class MySQLManagerOB(BaseMySQLManager):
    def __init__(self):
        super().__init__(use_scopefunc=True)
