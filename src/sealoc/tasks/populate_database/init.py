"""
Module for Initializing a database with ORM tables.
"""

import sealoc.database as db
import sealoc.orm as orm

from loguru import logger

from .types import InitializeDatabaseCommand


def run_init_database(command: InitializeDatabaseCommand) -> None:
    """
    Initialize a database by creating tables for ORM models.

    Arguments
    ---------
    command: Command containing the database URL and clear flag.
    """
    engine: db.Engine = db.create_engine(url=command.database_url)

    if command.clear_database:
        orm.close_all_sessions()
        orm.clear_orm_tables(engine)
        logger.info("Cleared ORM database tables!")

    # Initialize database tables
    orm.create_orm_tables(engine)

    table_names: list[str] = orm.get_orm_tables()

    logger.info("Created ORM database tables!")
    for table_name in table_names:
        logger.info(f" - {table_name}")
