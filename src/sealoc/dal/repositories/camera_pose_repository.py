"""
Repository for reading camera poses from a database session.
"""

import sealoc.database as db
import sealoc.orm as orm
import sealoc.models as models

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import batched
from typing import Any

from ..model_mappers import to_model


# NOTE: Variable limit is 999 for SQLite < 3.32.0, and 32766 for SQLite >= 3.32.0
VARIABLE_LIMIT: int = 999


@dataclass(frozen=True)
class CameraPoseRepository:
    """
    Repository for querying camera poses and mapping them to domain models.

    The repository wraps a database session, reads 'CameraPoseRecord' ORM objects,
    and returns mapped 'CameraPose' domain models.

    Attributes
    ----------
    session: Database session used for all queries.
    """

    session: db.Session

    record_type = orm.CameraPoseRecord
    model_type = models.CameraPose

    def get_all_ids(self) -> list[int]:
        """
        Retrieve all camera pose ids.

        Returns
        -------
        List of all camera pose ids.
        """
        statement = db.select(orm.CameraPoseRecord.camera_id)
        result = self.session.exec(statement)
        return list(result.all())

    def get_by_id(self, camera_id: int) -> models.CameraPose | None:
        """
        Retrieve a camera pose by its camera id.

        Arguments
        ---------
        camera_id: Camera id to look up.

        Returns
        -------
        Matching CameraPose, or None if not found.
        """
        record: orm.CameraPoseRecord | None = self.session.get(
            orm.CameraPoseRecord, camera_id
        )
        return to_model(record) if record else None

    def get_all_by_ids(self, camera_ids: Iterable[int]) -> list[models.CameraPose]:
        """
        Retrieve all camera poses with a camera id in the given collection.

        Queries in batches to avoid SQLite variable limits.

        Arguments
        ---------
        camera_ids: Camera ids to look up.

        Returns
        -------
        List of matching CameraPose models.
        """
        aggregated_poses: list[models.CameraPose] = list()

        # Select poses in batches to avoid too many variables error
        for batch in batched(camera_ids, VARIABLE_LIMIT):
            statement = db.select(orm.CameraPoseRecord).where(
                orm.CameraPoseRecord.camera_id.in_(batch)  # type: ignore[attr-defined]
            )
            result = self.session.exec(statement)
            aggregated_poses.extend([to_model(record) for record in result.all()])
        return aggregated_poses

    def get_one_by(self, **filters: Any) -> models.CameraPose | None:
        """
        Retrieve the first camera pose matching the given attribute filters.

        Arguments
        ---------
        **filters: Attribute name/value pairs to filter by.

        Returns
        -------
        First matching CameraPose, or None if not found.
        """
        statement = self._build_select_statement(filters)
        result = self.session.exec(statement)
        record = result.first()
        return to_model(record) if record else None

    def get_all_by(self, **filters: Any) -> list[models.CameraPose]:
        """
        Retrieve all camera poses matching the given attribute filters.

        Arguments
        ---------
        **filters: Attribute name/value pairs to filter by.

        Returns
        -------
        List of all matching CameraPose models.
        """
        statement = self._build_select_statement(filters)
        result = self.session.exec(statement)
        return [to_model(record) for record in result.all()]

    def _build_select_statement(self, filters: dict[str, Any]):
        """
        Build a select statement for camera poses with optional attribute filters.

        Arguments
        ---------
        filters: Attribute name/value pairs to filter by.

        Returns
        -------
        Select statement with all non-None filters applied.
        """
        filters = filters or {}
        statement = db.select(orm.CameraPoseRecord)
        for field_name, value in filters.items():
            if value is None:
                continue
            column = getattr(orm.CameraPoseRecord, field_name)
            statement = statement.where(column == value)
        return statement
