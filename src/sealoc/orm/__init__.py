"""
Package for sealocs ORM functionality.
"""

import sqlalchemy as sqla
import sqlmodel as sqlm

import sealoc.database as db

from .camera_records import (
    CameraBundleRecord as CameraBundleRecord,
    CameraCalibrationRecord as CameraCalibrationRecord,
    CameraFootprintRecord as CameraFootprintRecord,
    CameraGroupRecord as CameraGroupRecord,
    CameraPoseRecord as CameraPoseRecord,
    CameraRecord as CameraRecord,
    CameraSensorRecord as CameraSensorRecord,
)


def close_all_sessions() -> None:
    """Close all SQLAlchemy sessions."""
    sqla.orm.session.close_all_sessions()


def create_orm_tables(engine: db.Engine) -> None:
    """
    Create database tables based on the schema of the imported SQL models.

    Arguments
    ---------
    engine: Database engine to create the tables in.
    """
    sqlm.SQLModel.metadata.create_all(engine)


def clear_orm_tables(engine: db.Engine) -> None:
    """
    Drop all SQLModel tables in a database.

    Arguments
    ---------
    engine: Database engine to drop the tables from.
    """
    close_all_sessions()
    sqlm.SQLModel.metadata.drop_all(engine)


def get_orm_tables() -> list[str]:
    """
    Return the names of the SQLModel tables.

    Returns
    -------
    List of table names registered in the SQLModel metadata.
    """
    return list(sqlm.SQLModel.metadata.tables.keys())


__all__ = []
