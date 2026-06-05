"""
Module for data types for database building tasks.
"""

import pandas as pd  # type: ignore[import-untyped]

import sealoc.orm as orm

from dataclasses import (
    dataclass,
    field,
)
from pathlib import Path


@dataclass
class CameraDataTables:
    """
    Collection of camera data tables loaded from CSV files.

    Attributes
    ----------
    camera_calibrations: Calibration data table.
    camera_sensors: Sensor data table.
    cameras: Camera data table.
    camera_groups: Camera group data table.
    camera_bundles: Camera bundle data table.
    camera_poses: Camera pose data table.
    camera_footprints: Camera footprint data table.
    """

    camera_calibrations: pd.DataFrame
    camera_sensors: pd.DataFrame
    cameras: pd.DataFrame
    camera_groups: pd.DataFrame
    camera_bundles: pd.DataFrame
    camera_poses: pd.DataFrame
    camera_footprints: pd.DataFrame

    @property
    def frames(self) -> list[pd.DataFrame]:
        """
        Return the data frames in the tables object.

        Returns
        -------
        List of all data frames in the collection.
        """
        return [
            self.camera_calibrations,
            self.camera_sensors,
            self.cameras,
            self.camera_groups,
            self.camera_bundles,
            self.camera_poses,
            self.camera_footprints,
        ]


@dataclass
class InitializeDatabaseCommand:
    """
    Command for initializing a database with ORM models.

    Attributes
    ----------
    database_url: URL of the database to initialize.
    clear_database: Whether to drop existing tables before creating new ones.
    """

    database_url: str
    clear_database: bool = False


@dataclass
class PopulateDatabaseCommand:
    """
    Command for populating a database with camera data.

    Attributes
    ----------
    database_url: URL of the database to populate.
    input_dir: Directory containing the camera CSV files.
    """

    database_url: str
    input_dir: Path


@dataclass(slots=True)
class PopulateDatabaseContext:
    """
    Context type for building a camera database from files.

    Attributes
    ----------
    camera_tables: Loaded camera data tables, or None before loading.
    """

    camera_tables: CameraDataTables | None = field(default=None)


@dataclass(slots=True)
class PopulateDatabaseState:
    """
    State type for populating a database with camera data.

    Attributes
    ----------
    camera_calibrations: Built calibration records.
    camera_sensors: Built sensor records.
    cameras: Built camera records.
    camera_groups: Built camera group records.
    camera_bundles: Built camera bundle records.
    camera_poses: Built camera pose records.
    camera_footprints: Built camera footprint records.
    """

    camera_calibrations: list[orm.CameraCalibrationRecord] = field(default_factory=list)
    camera_sensors: list[orm.CameraSensorRecord] = field(default_factory=list)
    cameras: list[orm.CameraRecord] = field(default_factory=list)
    camera_groups: list[orm.CameraGroupRecord] = field(default_factory=list)
    camera_bundles: list[orm.CameraBundleRecord] = field(default_factory=list)
    camera_poses: list[orm.CameraPoseRecord] = field(default_factory=list)
    camera_footprints: list[orm.CameraFootprintRecord] = field(default_factory=list)

    def get_calibration_map(self) -> dict[int, orm.CameraCalibrationRecord]:
        """
        Return a mapping from id to calibration record.

        Returns
        -------
        Dict mapping calibration id to CameraCalibrationRecord.
        """
        return {
            calibration.id: calibration
            for calibration in self.camera_calibrations
            if calibration.id is not None
        }

    def get_sensor_map(self) -> dict[int, orm.CameraSensorRecord]:
        """
        Return a mapping from id to sensor record.

        Returns
        -------
        Dict mapping sensor id to CameraSensorRecord.
        """
        return {
            sensor.id: sensor for sensor in self.camera_sensors if sensor.id is not None
        }

    def get_camera_map(self) -> dict[int, orm.CameraRecord]:
        """
        Return a mapping from id to camera record.

        Returns
        -------
        Dict mapping camera id to CameraRecord.
        """
        return {camera.id: camera for camera in self.cameras if camera.id is not None}

    def get_camera_groups(self) -> dict[int, orm.CameraGroupRecord]:
        """
        Return a mapping from id to camera group record.

        Returns
        -------
        Dict mapping camera group id to CameraGroupRecord.
        """
        return {group.id: group for group in self.camera_groups if group.id is not None}

    def get_camera_bundles(self) -> dict[int, orm.CameraBundleRecord]:
        """
        Return a mapping from id to camera bundle record.

        Returns
        -------
        Dict mapping camera bundle id to CameraBundleRecord.
        """
        return {
            bundle.id: bundle for bundle in self.camera_bundles if bundle.id is not None
        }
