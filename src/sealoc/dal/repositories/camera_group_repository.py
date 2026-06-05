"""
Repository for reading camera group domain models from the database.
"""

import sealoc.database as db
import sealoc.orm as orm
import sealoc.models as models

from dataclasses import dataclass
from typing import Any

from ..model_mappers import to_model


@dataclass(frozen=True)
class CameraGroupRepository:
    """
    Repository for querying camera group records and mapping them to domain models.

    The repository wraps a database session, reads `CameraGroupRecord` ORM objects,
    and returns mapped `CameraGroup` domain models.

    Attributes
    ----------
    session: Database session used for all queries.
    """

    session: db.Session
    record_type = orm.CameraGroupRecord
    model_type = models.CameraGroup

    def get_all_ids(self) -> set[int]:
        """
        Retrieve all camera group record ids.

        Returns
        -------
        Set of all camera group ids.
        """
        statement = db.select(orm.CameraGroupRecord.id)
        result = self.session.exec(statement)
        return {id for id in result.all() if id is not None}

    def get_by_id(self, id: int) -> models.CameraGroup | None:
        """
        Retrieve a camera group by its id.

        Arguments
        ---------
        id: Camera group id to look up.

        Returns
        -------
        Matching CameraGroup, or None if not found.
        """
        record: orm.CameraGroupRecord | None = self.session.get(
            orm.CameraGroupRecord, id
        )
        return to_model(record) if record else None

    def get_one_by(self, **filters: Any) -> models.CameraGroup | None:
        """
        Retrieve the first camera group matching the given attribute filters.

        Arguments
        ---------
        **filters: Attribute name/value pairs to filter by.

        Returns
        -------
        First matching CameraGroup, or None if not found.
        """
        statement = self._build_select_statement(filters)
        result = self.session.exec(statement)
        record = result.first()
        return to_model(record) if record else None

    def get_all_by(self, **filters: Any) -> list[models.CameraGroup]:
        """
        Retrieve all camera groups matching the given attribute filters.

        Arguments
        ---------
        **filters: Attribute name/value pairs to filter by.

        Returns
        -------
        List of all matching CameraGroup models.
        """
        statement = self._build_select_statement(filters)
        result = self.session.exec(statement)
        return [to_model(record) for record in result.all()]

    def _build_select_statement(self, filters: dict[str, Any]):
        """
        Build a select statement for camera groups with optional attribute filters.

        Arguments
        ---------
        filters: Attribute name/value pairs to filter by.

        Returns
        -------
        Select statement with all non-None filters applied.
        """
        filters = filters or {}
        statement = db.select(orm.CameraGroupRecord)
        for field_name, value in filters.items():
            if value is None:
                continue
            column = getattr(orm.CameraGroupRecord, field_name)
            statement = statement.where(column == value)
        return statement
