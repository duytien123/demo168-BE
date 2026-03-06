from contextlib import contextmanager
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.constants.enum import SchemaType
from app.constants.message import Message
from app.context.db.base_mysql import MySQLManager
from app.log import logger
from app.middleware.secret import get_current_active_user
from app.middleware.location_context import get_location_context, LocationContext
from app.config import Settings

settings = Settings()


def get_db_primary_common(mysql_manager=Depends(MySQLManager.Instance)) -> Generator[Session, None, None]:
    """
       Dependency function to provide a MySQL database session for common

       This function yields a SQLAlchemy session for MySQL. It handles the creation and cleanup of the session, ensuring that any exceptions are logged and the session is rolled back if necessary.

       Args:
           mysql_manager (MySQLManager): Dependency injection for MySQLManager instance.

       Yields:
           Session: A SQLAlchemy session for MySQL.

       Raises:
           ValueError: If the user is not found.
           SQLAlchemyError: If an error occurs with the SQLAlchemy session.
       """

    database_name = settings.common_db_name
    mysql_session: Session = mysql_manager.get_session(database_name, SchemaType.COMMON.value)
    try:
        yield mysql_session
    except Exception as e:
        logger.error(Message.Database.CONNECT_MYSQL_ERROR, exc_info=e)
        mysql_session.rollback()
        raise e
    finally:
        try:
            mysql_session.expunge_all()
            mysql_session.close()
        finally:
            mysql_manager.remove()


def get_db_primary_ward_teannt(
        mysql_manager=Depends(MySQLManager.Instance), location: LocationContext=Depends(get_location_context)) -> Generator[Session, None, None]:
    """
        Dependency function to provide a MySQL database session for outbound operations based on the tenant ID of the current user.

        This function yields a SQLAlchemy session for MySQL. It handles the creation and cleanup of the session, ensuring that any exceptions are logged and the session is rolled back if necessary.

        Args:
            mysql_manager (MySQLManager): Dependency injection for MySQLManager instance.
            user (dict): The current active user, used to determine the tenant ID.

        Yields:
            Session: A SQLAlchemy session for MySQL.

        Raises:
            ValueError: If the user is not found.
            SQLAlchemyError: If an error occurs with the SQLAlchemy session.
        """

    if not location:
        raise ValueError(Message.User.USER_IS_NOT_FOUND)
    database_name = location.province_key + "_" + location.ward_key
    mysql_session: Session = mysql_manager.get_session(database_name, SchemaType.TENANT.value)  # noqa
    try:
        yield mysql_session
    except Exception as e:
        logger.error(Message.Database.CONNECT_MYSQL_ERROR, exc_info=e)
        mysql_session.rollback()
        raise e
    finally:
        try:
            mysql_session.expunge_all()
            mysql_session.close()
        finally:
            mysql_manager.remove()


@contextmanager
def get_thread_scoped_tenant_session(schema_tenant: str) -> Generator[Session, None, None]:
    """
    Dependency function to provide a MySQL session for a specific tenant based on the given tenant ID.
    This function creates and manages a SQLAlchemy session for MySQL, handling both tenant's inbound, outbound and common databases.
    It ensures proper session creation and cleanup, logs errors, and rolls back the session if necessary.
    Args:
        tenant_id (str): The tenant's unique identifier used to resolve the correct database connection.
    Yields:
        Session: A SQLAlchemy session for MySQL.
    Raises:
        ValueError: If the user is not found.
        SQLAlchemyError: If an error occurs with the SQLAlchemy session.
    """
    mysql_manager = MySQLManager.Instance()
    mysql_session: Session = mysql_manager.get_tenant_session(
        schema_tenant
    )
    try:
        with mysql_session.begin():
            yield mysql_session
    except Exception as e:
        logger.error(Message.Database.CONNECT_MYSQL_ERROR, exc_info=e)
        mysql_session.rollback()
        raise e
    finally:
        try:
            mysql_session.expunge_all()
            mysql_session.close()
        finally:
            mysql_manager.remove()


@contextmanager
def get_db_from_schema_name(schema: str, schema_type: str):
    """
       Context manager to provide a MySQL database session based on the given schema name.

       This function yields a SQLAlchemy session for MySQL. It handles the creation and cleanup of the session, ensuring that any exceptions are logged and the session is rolled back if necessary.

       Args:
            schema (str): The schema name to be used for the MySQL session.
            schema_type (str): The schema type to be used for the MySQL session.
       Yields:
           Session: A SQLAlchemy session for MySQL.

       Raises:
           SQLAlchemyError: If an error occurs with the SQLAlchemy session.
       """
    _mysql_session = MySQLManager.Instance().independ_schema_session(schema, schema_type)  # noqa
    session = _mysql_session()
    mysql_session: Session = session
    try:
        yield mysql_session
    except Exception as e:
        logger.error(Message.Database.CONNECT_MYSQL_ERROR, exc_info=e)
        mysql_session.rollback()
        raise e
    finally:
        try:
            mysql_session.expunge_all()
            mysql_session.close()
        finally:
            MySQLManager.Instance().remove()


@contextmanager
def transaction_primary(db_primary: Session, db_primary_ob: Session):
    """
       Start transactions for primary and outbound MySQL databases.

       This context manager synchronizes transactions across the primary and outbound MySQL databases.
       When declared within a `with` block, it ensures that transactions for both databases are started simultaneously and managed together.

       Args:
           db_primary (Session): SQLAlchemy session for the primary MySQL database.
           db_primary_ob (Session): SQLAlchemy session for the outbound MySQL database.

       Yields:
           None: This context manager does not return any value.

       Example:
           with transaction_primary(db_primary, db_primary_ob):
               # Perform database operations here
       """

    if not db_primary.in_transaction() and not db_primary_ob.in_transaction():
        with db_primary.begin(), \
                db_primary_ob.begin():
            yield
    else:
        yield


def get_tenant_session(
        mysql_manager=Depends(MySQLManager.Instance),
        user=Depends(get_current_active_user)
) -> Generator[Session, None, None]:
    """
    Dependency function to provide a MySQL session for both inbound, outbound and common based on the current tenant information.

    This function creates and manages a SQLAlchemy session for MySQL, handling both tenant's inbound, outbound and common databases.
    It ensures proper session creation and cleanup, logs errors, and rolls back the session if necessary.

    Args:
        mysql_manager (MySQLManager): Dependency injection for MySQLManager instance.
        user (dict): The current active user, used to determine database names.

    Yields:
        Session: A SQLAlchemy session for MySQL.

    Raises:
        ValueError: If the user is not found.
        SQLAlchemyError: If an error occurs with the SQLAlchemy session.
    """

    if not user:
        raise ValueError(Message.User.USER_IS_NOT_FOUND)

    database_name_ob = user["database_name_ob"]
    database_name_ib = user["company"]
    mysql_session: Session = mysql_manager.get_tenant_session(
        database_name_ob,
        database_name_ib,
    )
    try:
        yield mysql_session
    except Exception as e:
        logger.error(Message.Database.CONNECT_MYSQL_ERROR, exc_info=e)
        mysql_session.rollback()
        raise e
    finally:
        try:
            mysql_session.expunge_all()
            mysql_session.close()
        finally:
            mysql_manager.remove()


def get_base_session(
        mysql_manager=Depends(MySQLManager.Instance)):
    session_all: Session = mysql_manager.get_session_all()

    try:
        yield session_all
    except Exception as e:
        logger.error(Message.Database.CONNECT_MYSQL_ERROR, exc_info=e)
        session_all.rollback()
        raise e
    finally:
        try:
            session_all.expunge_all()
            session_all.close()
        finally:
            mysql_manager.remove()
