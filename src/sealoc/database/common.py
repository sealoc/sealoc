"""
Module for common database functionality.
"""

import contextlib
import sqlalchemy as sqla

from collections.abc import Generator
from pathlib import Path
from sqlmodel import select as select

from .types import (
    Engine,
    Session,
)


def validate_database_url(url: str) -> None:
    """
    Validate a database URL, raising an error for missing SQLite files.

    Arguments
    ---------
    url: Database URL string to validate.
    """
    parsed: sqla.engine.URL = sqla.engine.make_url(url)
    if parsed.get_dialect().name == "sqlite":
        db_path: str | None = parsed.database
        if db_path and db_path != ":memory:" and not Path(db_path).is_file():
            raise FileNotFoundError(f"database file not found: {db_path}")


def create_engine(
    *,
    url: str,
    verbose: bool = False,
) -> Engine:
    """
    Create an engine for connecting to a database.

    Arguments
    ---------
    url: Database URL string.
    verbose: Whether to echo SQL statements. Defaults to False.

    Returns
    -------
    Database engine connected to the given URL.
    """
    return sqla.create_engine(url, echo=verbose)


@contextlib.contextmanager
def session_scope(engine: Engine) -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of database operations.

    Commits on success and rolls back on exception.

    Arguments
    ---------
    engine: Database engine to open the session against.

    Yields
    ------
    Open database session bound to the given engine.
    """
    session: Session = Session(engine)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
