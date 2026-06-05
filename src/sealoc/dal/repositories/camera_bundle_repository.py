"""
Repository for reading camera bundle domain models from the database.
"""

import sealoc.database as db
import sealoc.orm as orm
import sealoc.models as models

from dataclasses import dataclass
from typing import Any

from ..model_mappers import to_model


@dataclass(slots=True, frozen=True)
class CameraBundleRepository:
    """
    Repository for querying camera bundle records and mapping them to domain models.

    The repository wraps a database session, reads `CameraBundleRecord` ORM objects,
    and returns mapped `CameraBundle` domain models.

    Attributes
    ----------
    session: Database session used for all queries.
    """

    session: db.Session

    record_type = orm.CameraBundleRecord
    model_type = models.CameraBundle

    def get_all_ids(self) -> set[int]:
        """
        Retrieve all camera bundle record ids.

        Returns
        -------
        Set of all camera bundle ids.
        """
        statement = db.select(orm.CameraBundleRecord.id)
        result = self.session.exec(statement)
        return {id for id in result.all() if id is not None}

    def get_by_id(self, id: int) -> models.CameraBundle | None:
        """
        Retrieve a camera bundle by its id.

        Arguments
        ---------
        id: Camera bundle id to look up.

        Returns
        -------
        Matching CameraBundle, or None if not found.
        """
        record: orm.CameraBundleRecord | None = self.session.get(
            orm.CameraBundleRecord, id
        )
        return to_model(record) if record else None

    def get_one_by(self, **filters: Any) -> models.CameraBundle | None:
        """
        Retrieve the first camera bundle matching the given attribute filters.

        Arguments
        ---------
        **filters: Attribute name/value pairs to filter by.

        Returns
        -------
        First matching CameraBundle, or None if not found.
        """
        statement = self._build_select_statement(filters)
        result = self.session.exec(statement)
        record = result.first()
        return to_model(record) if record else None

    def get_all_by(self, **filters: Any) -> list[models.CameraBundle]:
        """
        Retrieve all camera bundles matching the given attribute filters.

        Arguments
        ---------
        **filters: Attribute name/value pairs to filter by.

        Returns
        -------
        List of all matching CameraBundle models.
        """
        statement = self._build_select_statement(filters)
        result = self.session.exec(statement)
        return [to_model(record) for record in result.all()]

    def _build_select_statement(self, filters: dict[str, Any]):
        """
        Build a select statement for camera bundles with optional attribute filters.

        Arguments
        ---------
        filters: Attribute name/value pairs to filter by.

        Returns
        -------
        Select statement with all non-None filters applied.
        """
        filters = filters or {}
        statement = db.select(orm.CameraBundleRecord)
        for field_name, value in filters.items():
            if value is None:
                continue
            column = getattr(orm.CameraBundleRecord, field_name)
            statement = statement.where(column == value)
        return statement
