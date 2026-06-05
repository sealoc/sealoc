"""
Event handlers for validating camera master–slave consistency.

Checks that master–slave relationships between CameraRecord instances
match the corresponding relationships between their CameraSensorRecord
instances before changes are flushed to the database.
"""

import sqlalchemy as sqla

import sealoc.database as db

from typing import (
    Any,
    Sequence,
)

from .camera_records import (
    CameraRecord,
    CameraSensorRecord,
)


@sqla.event.listens_for(db.Session, "before_flush")
def validate_master_camera_sensor(
    session: db.Session,
    flush_context: Any,
    instances: Sequence[Any],
) -> None:
    """
    Ensure camera and sensor master–slave relationships are consistent before flush.

    For each CameraRecord with a master_camera, verifies that both cameras have sensors
    and that the master's sensor is the master of the slave's sensor. Raises ValueError
    if the invariant is violated.

    Arguments
    ---------
    session: The database session being flushed.
    flush_context: SQLAlchemy flush context (unused).
    instances: Instances passed to the flush (unused).
    """
    # Only validate new/dirty CameraRecord objects
    to_check: list[Any] = list(session.new) + list(session.dirty)

    camera_records: list[CameraRecord] = [
        item for item in to_check if isinstance(item, CameraRecord)
    ]

    for camera_record in camera_records:
        # Only slave cameras with a master
        if camera_record.master_camera is None:
            continue

        slave_camera: CameraRecord = camera_record
        master_camera: CameraRecord = camera_record.master_camera

        # If sensors are not attached yet, either skip or enforce your own rule
        slave_sensor: CameraSensorRecord = slave_camera.sensor
        master_sensor: CameraSensorRecord = master_camera.sensor

        if slave_sensor is None or master_sensor is None:
            raise ValueError("master and slave camera sensors are none")

        if slave_sensor.master_sensor is not master_sensor:
            raise ValueError(
                "Sensor of master camera must be the master of the slave camera's sensor."
            )
