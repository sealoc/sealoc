"""
Module with builder functions.
"""

import pandas as pd  # type: ignore[import-untyped]

import sealoc.database as db
import sealoc.orm as orm

from loguru import logger

from .types import (
    CameraDataTables,
    PopulateDatabaseState,
)


def build_records_from_tables(
    session: db.Session, tables: CameraDataTables
) -> PopulateDatabaseState:
    """
    Build and persist all camera ORM records from the given data tables.

    Arguments
    ---------
    session: Database session to add records to.
    tables: Camera data tables loaded from CSV files.

    Returns
    -------
    PopulateDatabaseState containing all built records.
    """
    state: PopulateDatabaseState = PopulateDatabaseState()
    summary: list[str] = list()

    # Build camera bundles
    _build_camera_bundles(state, tables)
    summary.append(f"Built {len(state.camera_bundles)} camera bundles.")

    # Build camera groups
    _build_camera_groups(state, tables)
    summary.append(f"Built {len(state.camera_groups)} camera groups.")

    # Build camera calibrations
    _build_camera_calibrations(state, tables)
    summary.append(f"Built {len(state.camera_calibrations)} camera calibrations.")

    # Build camera sensors
    _build_camera_sensors(state, tables)
    summary.append(f"Built {len(state.camera_sensors)} camera sensors.")

    # Build cameras
    _build_cameras(state, tables)
    summary.append(f"Built {len(state.cameras)} cameras.")

    # Build camera poses
    _build_camera_poses(state, tables)
    summary.append(f"Built {len(state.camera_poses)} camera poses.")

    # Build camera footprints
    _build_camera_footprints(state, tables)
    summary.append(f"Built {len(state.camera_footprints)} camera footprints.")

    logger.info("Processing summary:\n" + "\n".join(f"- {line}" for line in summary))

    # ----------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------

    # Relate camera groups to bundles
    _relate_groups_to_bundles(state, tables)
    # Relate camera sensors to groups
    _relate_sensors_to_groups(state, tables)
    # Relate cameras to groups
    _relate_cameras_to_groups(state, tables)
    # Relate cameras to camera sensors
    _relate_cameras_to_sensors(state, tables)
    # Relate sensor to calibration
    _relate_sensors_to_calibrations(state, tables)
    # Relate sensor to master
    _relate_sensors_to_sensors(state, tables)
    # Relate camera to master
    _relate_cameras_to_cameras(state, tables)

    for bundle in state.camera_bundles:
        session.add(bundle)
    for group in state.camera_groups:
        session.add(group)
    for sensor in state.camera_sensors:
        session.add(sensor)
    for calibration in state.camera_calibrations:
        session.add(calibration)
    for camera in state.cameras:
        session.add(camera)
    for camera_pose in state.camera_poses:
        session.add(camera_pose)
    for camera_footprint in state.camera_footprints:
        session.add(camera_footprint)

    session.commit()

    logger.info("Committed camera data!")

    return state


def _build_camera_bundles(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Build camera bundle records from the table data.

    Arguments
    ---------
    state: State object to append the built records to.
    tables: Camera data tables containing bundle rows.
    """
    required_columns: set[str] = {"camera_bundle_id", "camera_bundle_label", "meta"}
    if not required_columns.issubset(tables.camera_bundles.columns):
        raise ValueError(f"missing required columns: {required_columns}")

    for index, row in tables.camera_bundles.iterrows():
        camera_bundle: orm.CameraBundleRecord = orm.CameraBundleRecord(
            id=row.get("camera_bundle_id"),
            label=row.get("camera_bundle_label"),
            meta=row.get("meta"),
        )
        state.camera_bundles.append(camera_bundle)


def _build_camera_groups(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Build camera group records from the table data.

    Arguments
    ---------
    state: State object to append the built records to.
    tables: Camera data tables containing group rows.
    """
    required_columns: set[str] = {"camera_group_id", "camera_group_label", "meta"}
    if not required_columns.issubset(tables.camera_groups.columns):
        raise ValueError(f"missing required columns: {required_columns}")

    for index, row in tables.camera_groups.iterrows():
        camera_group: orm.CameraGroupRecord = orm.CameraGroupRecord(
            id=row.get("camera_group_id"),
            label=row.get("camera_group_label"),
            meta=row.get("meta"),
        )
        state.camera_groups.append(camera_group)


def _build_camera_calibrations(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Build camera calibration records from table rows.

    Arguments
    ---------
    state: State object to append the built records to.
    tables: Camera data tables containing calibration rows.
    """
    required_columns: set[str] = {
        "calibration_id",
        "width",
        "height",
        "fx",
        "fy",
        "cx",
        "cy",
        "k1",
        "k2",
        "k3",
        "p1",
        "p2",
    }
    if not required_columns.issubset(tables.camera_calibrations.columns):
        raise ValueError(
            f"missing required columns: {required_columns.difference(tables.camera_calibrations.columns)}"
        )

    for index, row in tables.camera_calibrations.iterrows():
        calibration: orm.CameraCalibrationRecord = orm.CameraCalibrationRecord(
            id=row.get("calibration_id"),
            width=row.get("width"),
            height=row.get("height"),
            fx=row.get("fx"),
            fy=row.get("fy"),
            cx=row.get("cx"),
            cy=row.get("cy"),
            k1=row.get("k1"),
            k2=row.get("k2"),
            k3=row.get("k3"),
            p1=row.get("p1"),
            p2=row.get("p2"),
        )

        state.camera_calibrations.append(calibration)


def _build_camera_sensors(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Build camera sensor records from table rows.

    Arguments
    ---------
    state: State object to append the built records to.
    tables: Camera data tables containing sensor rows.
    """
    required_columns: set[str] = {
        "sensor_id",
        "sensor_label",
        "sensor_width",
        "sensor_height",
        "sensor_location",
        "sensor_rotation",
    }
    if not required_columns.issubset(tables.camera_sensors.columns):
        raise ValueError(
            f"missing required columns: {required_columns.difference(tables.camera_sensors.columns)}"
        )

    for index, row in tables.camera_sensors.iterrows():
        camera_sensor: orm.CameraSensorRecord = orm.CameraSensorRecord(
            id=row.get("sensor_id"),
            label=row.get("sensor_label"),
            width=row.get("sensor_width"),
            height=row.get("sensor_height"),
            location=row.get("sensor_location"),
            rotation=row.get("sensor_rotation"),
        )
        state.camera_sensors.append(camera_sensor)


def _build_cameras(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Build camera records from table rows.

    Arguments
    ---------
    state: State object to append the built records to.
    tables: Camera data tables containing camera rows.
    """
    required_columns: set[str] = {
        "camera_id",
        "camera_label",
        "image_label",
        "meta",
    }
    if not required_columns.issubset(tables.cameras.columns):
        raise ValueError(
            f"missing required columns: {required_columns.difference(tables.cameras.columns)}"
        )

    for index, row in tables.cameras.iterrows():
        camera: orm.CameraRecord = orm.CameraRecord(
            id=row.get("camera_id"),
            label=row.get("camera_label"),
            image_label=row.get("image_label"),
            meta=row.get("meta"),
        )
        state.cameras.append(camera)


def _build_camera_poses(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Build camera pose records from table rows.

    Arguments
    ---------
    state: State object to append the built records to.
    tables: Camera data tables containing pose rows.
    """
    required_columns: set[str] = {
        "camera_id",
        "longitude",
        "latitude",
        "height",
        "yaw",
        "pitch",
        "roll",
    }

    if not required_columns.issubset(tables.camera_poses.columns):
        raise ValueError(
            f"missing required columns: {required_columns.difference(tables.camera_poses.columns)}"
        )

    for index, row in tables.camera_poses.iterrows():
        camera_pose: orm.CameraPoseRecord = orm.CameraPoseRecord(
            camera_id=row["camera_id"],
            location=(row["longitude"], row["latitude"], row["height"]),
            srid=4326,
            yaw=row["yaw"],
            pitch=row["pitch"],
            roll=row["roll"],
        )
        state.camera_poses.append(camera_pose)


def _build_camera_footprints(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Build camera footprint records from table rows.

    Arguments
    ---------
    state: State object to append the built records to.
    tables: Camera data tables containing footprint rows.
    """
    required_columns: set[str] = {
        "camera_id",
        "coordinates",
    }

    if not required_columns.issubset(tables.camera_footprints.columns):
        raise ValueError(
            f"missing required columns: {required_columns.difference(tables.camera_footprints.columns)}"
        )

    for index, row in tables.camera_footprints.iterrows():
        camera_footprint: orm.CameraFootprintRecord = orm.CameraFootprintRecord(
            camera_id=row["camera_id"],
            polygon=row["coordinates"],
            srid=4326,
        )

        state.camera_footprints.append(camera_footprint)


def _relate_groups_to_bundles(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Relate camera groups to their parent camera bundles.

    Arguments
    ---------
    state: State containing the built bundle and group records.
    tables: Camera data tables containing group-to-bundle mappings.
    """
    camera_bundle_map: dict[int, orm.CameraBundleRecord] = {
        bundle.id: bundle for bundle in state.camera_bundles if bundle.id is not None
    }
    camera_group_map: dict[int, orm.CameraGroupRecord] = {
        group.id: group for group in state.camera_groups if group.id is not None
    }

    for index, row in tables.camera_groups.iterrows():
        camera_group_id: int | None = row["camera_group_id"]
        camera_bundle_id: int | None = row["camera_bundle_id"]

        if pd.isna(camera_bundle_id) or pd.isna(camera_group_id):
            continue

        assert isinstance(camera_group_id, int)
        assert isinstance(camera_bundle_id, int)

        if camera_group_id not in camera_group_map:
            raise ValueError(f"missing camera group: {camera_group_id}")

        if camera_bundle_id not in camera_bundle_map:
            raise ValueError(f"missing camera bundle: {camera_bundle_id}")

        camera_bundle: orm.CameraBundleRecord = camera_bundle_map[camera_bundle_id]
        camera_group: orm.CameraGroupRecord = camera_group_map[camera_group_id]

        camera_bundle.camera_groups.append(camera_group)


def _relate_sensors_to_groups(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Relate camera sensors to their parent camera groups.

    Arguments
    ---------
    state: State containing the built sensor and group records.
    tables: Camera data tables containing sensor-to-group mappings.
    """
    camera_sensor_map: dict[int, orm.CameraSensorRecord] = {
        sensor.id: sensor for sensor in state.camera_sensors if sensor.id is not None
    }
    camera_group_map: dict[int, orm.CameraGroupRecord] = {
        group.id: group for group in state.camera_groups if group.id is not None
    }

    for index, row in tables.camera_sensors.iterrows():
        camera_sensor_id: int | None = row["sensor_id"]
        camera_group_id: int | None = row["camera_group_id"]

        if pd.isna(camera_sensor_id) or pd.isna(camera_group_id):
            continue

        assert isinstance(camera_sensor_id, int)
        assert isinstance(camera_group_id, int)

        if camera_sensor_id not in camera_sensor_map:
            raise ValueError(f"missing camera sensor: {camera_sensor_id}")

        if camera_group_id not in camera_group_map:
            raise ValueError(f"missing camera group: {camera_group_id}")

        camera_sensor: orm.CameraSensorRecord = camera_sensor_map[camera_sensor_id]
        camera_group: orm.CameraGroupRecord = camera_group_map[camera_group_id]

        camera_group.sensors.append(camera_sensor)


def _relate_cameras_to_groups(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Relate cameras to their parent camera groups.

    Arguments
    ---------
    state: State containing the built camera and group records.
    tables: Camera data tables containing camera-to-group mappings.
    """
    camera_map: dict[int, orm.CameraRecord] = {
        camera.id: camera for camera in state.cameras if camera.id is not None
    }
    camera_group_map: dict[int, orm.CameraGroupRecord] = {
        group.id: group for group in state.camera_groups if group.id is not None
    }

    for index, row in tables.cameras.iterrows():
        camera_id: int | None = row["camera_id"]
        camera_group_id: int | None = row["camera_group_id"]

        if pd.isna(camera_id) or pd.isna(camera_group_id):
            continue

        assert isinstance(camera_id, int)
        assert isinstance(camera_group_id, int)

        if camera_id not in camera_map:
            raise ValueError(f"missing camera: {camera_id}")

        if camera_group_id not in camera_group_map:
            raise ValueError(f"missing camera group: {camera_group_id}")

        camera: orm.CameraRecord = camera_map[camera_id]
        camera_group: orm.CameraGroupRecord = camera_group_map[camera_group_id]

        camera_group.cameras.append(camera)


def _relate_cameras_to_sensors(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Relate cameras to their camera sensors.

    Arguments
    ---------
    state: State containing the built camera and sensor records.
    tables: Camera data tables containing camera-to-sensor mappings.
    """
    camera_map: dict[int, orm.CameraRecord] = {
        camera.id: camera for camera in state.cameras if camera.id is not None
    }
    camera_sensor_map: dict[int, orm.CameraSensorRecord] = {
        sensor.id: sensor for sensor in state.camera_sensors if sensor.id is not None
    }

    for index, row in tables.cameras.iterrows():
        camera_id: int | None = row["camera_id"]
        camera_sensor_id: int | None = row["camera_sensor_id"]

        if pd.isna(camera_id) or pd.isna(camera_sensor_id):
            logger.warning("skipping camera-sensor row")
            continue

        assert isinstance(camera_id, int)
        assert isinstance(camera_sensor_id, int)

        if camera_id not in camera_map:
            raise ValueError(f"missing camera: {camera_id}")

        if camera_sensor_id not in camera_sensor_map:
            raise ValueError(f"missing camera sensor: {camera_sensor_id}")

        camera: orm.CameraRecord = camera_map[camera_id]
        camera_sensor: orm.CameraSensorRecord = camera_sensor_map[camera_sensor_id]

        camera.sensor = camera_sensor


def _relate_sensors_to_calibrations(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Relate camera sensors to their calibrations.

    Arguments
    ---------
    state: State containing the built sensor and calibration records.
    tables: Camera data tables containing sensor-to-calibration mappings.
    """
    sensor_map: dict[int, orm.CameraSensorRecord] = state.get_sensor_map()
    calibration_map: dict[int, orm.CameraCalibrationRecord] = (
        state.get_calibration_map()
    )

    for index, row in tables.camera_sensors.iterrows():
        sensor_id: int | None = row["sensor_id"]
        calibration_id: int | None = row["sensor_calibration_id"]

        assert isinstance(sensor_id, int)
        assert isinstance(calibration_id, int)

        camera_sensor: orm.CameraSensorRecord | None = sensor_map.get(sensor_id)
        calibration: orm.CameraCalibrationRecord | None = calibration_map.get(
            calibration_id
        )

        if camera_sensor is None:
            raise ValueError(f"missing sensor: {sensor_id}")

        if calibration is None:
            raise ValueError(f"missing calibration: {calibration_id}")

        camera_sensor.calibration = calibration


def _relate_sensors_to_sensors(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Relate slave camera sensors to their master sensors.

    Arguments
    ---------
    state: State containing the built sensor records.
    tables: Camera data tables containing master-slave sensor mappings.
    """
    sensor_map: dict[int, orm.CameraSensorRecord] = state.get_sensor_map()

    data_frame: pd.DataFrame = tables.camera_sensors.dropna(
        subset=["sensor_id", "master_sensor_id"], how="any"
    )

    for index, row in data_frame.iterrows():
        slave_sensor_id: int = int(row["sensor_id"])
        master_sensor_id: int = int(row["master_sensor_id"])

        slave_sensor: orm.CameraSensorRecord | None = sensor_map.get(slave_sensor_id)
        master_sensor: orm.CameraSensorRecord | None = sensor_map.get(master_sensor_id)

        if slave_sensor is None:
            raise ValueError(f"missing sensor: {slave_sensor_id}")
        if master_sensor is None:
            raise ValueError(f"missing sensor: {master_sensor_id}")

        slave_sensor.master_sensor = master_sensor


def _relate_cameras_to_cameras(
    state: PopulateDatabaseState,
    tables: CameraDataTables,
) -> None:
    """
    Relate slave cameras to their master cameras.

    Arguments
    ---------
    state: State containing the built camera records.
    tables: Camera data tables containing master-slave camera mappings.
    """
    camera_map: dict[int, orm.CameraRecord] = state.get_camera_map()

    data_frame: pd.DataFrame = tables.cameras.dropna(
        subset=["camera_id", "master_camera_id"], how="any"
    )

    for index, row in data_frame.iterrows():
        slave_camera_id: int = int(row["camera_id"])
        master_camera_id: int = int(row["master_camera_id"])

        slave_camera: orm.CameraRecord | None = camera_map.get(slave_camera_id)
        master_camera: orm.CameraRecord | None = camera_map.get(master_camera_id)

        if slave_camera is None:
            raise ValueError(f"missing camera: {slave_camera_id}")
        if master_camera is None:
            raise ValueError(f"missing camera: {master_camera_id}")

        slave_camera.master_camera = master_camera
