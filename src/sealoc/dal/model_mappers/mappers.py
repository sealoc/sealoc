"""
Module for mapping ORM models to domain models.
"""

import functools
import typing

import sealoc.orm as orm
import sealoc.models as models


@functools.singledispatch
def to_model(record: typing.Any) -> typing.Any:
    """
    Map an ORM record to its corresponding domain model.

    Arguments
    ---------
    record: ORM record to map.

    Returns
    -------
    Domain model corresponding to the record type.
    """
    raise NotImplementedError(f"No model mapping for type {type(record)}")


@to_model.register
def _(record: orm.CameraBundleRecord) -> models.CameraBundle:
    """
    Convert a camera bundle record to a camera bundle model.

    Arguments
    ---------
    record: Camera bundle ORM record.

    Returns
    -------
    Mapped CameraBundle domain model.
    """
    groups: list[models.CameraGroup] = [
        to_model(group) for group in record.camera_groups
    ]
    bundle: models.CameraBundle = models.CameraBundle(**record.model_dump())
    for group in groups:
        bundle.add_group(group)
    return bundle


@to_model.register
def _(record: orm.CameraGroupRecord) -> models.CameraGroup:
    """
    Convert a camera group record to a camera group model.

    Arguments
    ---------
    record: Camera group ORM record.

    Returns
    -------
    Mapped CameraGroup domain model.
    """
    group: models.CameraGroup = models.CameraGroup(**record.model_dump())

    # Convert sensor and camera records to models
    sensors: list[models.CameraSensor] = [to_model(sensor) for sensor in record.sensors]
    cameras: list[models.Camera] = [to_model(camera) for camera in record.cameras]

    # Convert camera poses and footprints
    camera_poses: list[models.CameraPose] = [
        to_model(camera.camera_pose) for camera in record.cameras if camera.camera_pose
    ]
    camera_footprints: list[models.CameraFootprint] = [
        to_model(camera.camera_footprint)
        for camera in record.cameras
        if camera.camera_footprint
    ]

    # Hydrate camera and camera sensor relationships
    _hydrate_camera_relationships(cameras, sensors)

    # Assign camera poses and footprints to cameras
    _assign_poses_to_cameras(cameras, camera_poses)
    _assign_footprints_to_cameras(cameras, camera_footprints)

    # Add sensors to the camera group
    for sensor in sensors:
        group.add_sensor(sensor)

    # Add cameras to the camera group
    for camera in cameras:
        group.add_camera(camera)

    return group


def _hydrate_camera_relationships(
    cameras: list[models.Camera],
    sensors: list[models.CameraSensor],
) -> None:
    """
    Rewire cameras and sensors to shared instances.

    Ensures all cameras use canonical sensor objects from sensors and that
    master–slave links between cameras and sensors point to these shared
    instances, raising ValueError if a referenced object is missing.

    Arguments
    ---------
    cameras: List of camera domain models to rewire.
    sensors: List of camera sensor domain models to use as canonical instances.
    """
    sensor_map: dict[int, models.CameraSensor] = {
        sensor.id: sensor for sensor in sensors
    }
    camera_map: dict[int, models.Camera] = {camera.id: camera for camera in cameras}

    # Reassign camera sensor
    for camera in cameras:
        if camera.sensor.id not in sensor_map:
            raise ValueError(f"missing camera sensor: {camera.sensor.id}")

        reference_sensor: models.CameraSensor = sensor_map[camera.sensor.id]
        camera.camera_sensor = reference_sensor

    # Reassign master-slave sensors - Common reference
    for sensor in sensors:
        if sensor.master_sensor is None:
            continue
        if sensor.master_sensor.id not in sensor_map:
            raise ValueError(f"missing master sensor id: {sensor.master_sensor.id}")

        master_sensor: models.CameraSensor = sensor_map[sensor.master_sensor.id]
        sensor.master_sensor = master_sensor

    # Reassign master-slave cameras - Common reference
    for camera in cameras:
        if camera.master_camera is None:
            continue
        if camera.master_camera.id not in camera_map:
            raise ValueError(f"missing master camera id: {camera.master_camera.id}")

        master_camera: models.Camera = camera_map[camera.master_camera.id]
        camera.master_camera = master_camera


def _assign_poses_to_cameras(
    cameras: list[models.Camera],
    camera_poses: list[models.CameraPose],
) -> None:
    """
    Assign poses to cameras by matching on camera id.

    Arguments
    ---------
    cameras: Camera domain models to assign poses to.
    camera_poses: Poses to assign.
    """
    pose_map: dict[int, models.CameraPose] = {
        pose.camera_id: pose for pose in camera_poses
    }
    for camera in cameras:
        if camera.id not in pose_map:
            continue
        camera.set_pose(pose_map[camera.id])


def _assign_footprints_to_cameras(
    cameras: list[models.Camera],
    camera_footprints: list[models.CameraFootprint],
) -> None:
    """
    Assign footprints to cameras by matching on camera id.

    Arguments
    ---------
    cameras: Camera domain models to assign footprints to.
    camera_footprints: Footprints to assign.
    """
    footprint_map: dict[int, models.CameraFootprint] = {
        footprint.camera_id: footprint for footprint in camera_footprints
    }
    for camera in cameras:
        if camera.id not in footprint_map:
            continue
        camera.set_footprint(footprint_map[camera.id])


@to_model.register
def _(calibration_record: orm.CameraCalibrationRecord) -> models.CameraCalibration:
    """
    Convert a camera calibration record to a camera calibration model.

    Arguments
    ---------
    calibration_record: Camera calibration ORM record.

    Returns
    -------
    Mapped CameraCalibration domain model.
    """
    data: dict = calibration_record.model_dump(exclude={"sensor"})
    return models.CameraCalibration.model_validate(data)


@to_model.register
def _(sensor_record: orm.CameraSensorRecord) -> models.CameraSensor:
    """
    Convert a camera sensor record to a camera sensor model.

    Arguments
    ---------
    sensor_record: Camera sensor ORM record.

    Returns
    -------
    Mapped CameraSensor domain model.
    """
    fields: dict = sensor_record.model_dump(
        exclude={"calibration", "camera_group", "location", "rotation"}
    )

    camera_calibration: models.CameraCalibration = to_model(sensor_record.calibration)
    location: tuple = _convert_sensor_location(sensor_record.location)
    rotation: tuple = _convert_sensor_rotation(sensor_record.rotation)

    fields["calibration"] = camera_calibration
    fields["location"] = location
    fields["rotation"] = rotation

    if sensor_record.master_sensor:
        master_sensor: models.CameraSensor = to_model(sensor_record.master_sensor)
        fields["master_sensor"] = master_sensor

    return models.CameraSensor.model_validate(fields)


def _convert_sensor_location(
    location: tuple[float, float, float] | None,
) -> tuple[float, float, float]:
    """
    Convert a sensor location to a 3-tuple, defaulting to origin if None.

    Arguments
    ---------
    location: XYZ location tuple, or None.

    Returns
    -------
    Location as a 3-tuple of floats, or (0.0, 0.0, 0.0) if None.
    """
    if location is None:
        return (0.0, 0.0, 0.0)
    return (location[0], location[1], location[2])


def _convert_sensor_rotation(
    rotation: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None,
) -> tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]:
    """
    Convert a sensor rotation to nested 3-tuples, defaulting to identity if None.

    Arguments
    ---------
    rotation: 3x3 rotation matrix as nested tuples, or None.

    Returns
    -------
    Rotation as nested 3-tuples of floats, or the identity matrix if None.
    """
    if rotation is None:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    return (
        (rotation[0][0], rotation[0][1], rotation[0][2]),
        (rotation[1][0], rotation[1][1], rotation[1][2]),
        (rotation[2][0], rotation[2][1], rotation[2][2]),
    )


@to_model.register
def _(camera_record: orm.CameraRecord) -> models.Camera:
    """
    Convert a camera record to a camera model.

    Arguments
    ---------
    camera_record: Camera ORM record.

    Returns
    -------
    Mapped Camera domain model.
    """
    fields: dict = camera_record.model_dump(exclude={"camera_sensor", "camera_group"})

    camera_sensor: models.CameraSensor = to_model(camera_record.sensor)
    fields["camera_sensor"] = camera_sensor

    if camera_record.master_camera:
        master_camera: models.Camera = to_model(camera_record.master_camera)
        fields["master_camera"] = master_camera

    return models.Camera.model_validate(fields)


@to_model.register
def _(camera_pose_record: orm.CameraPoseRecord) -> models.CameraPose:
    """
    Convert a camera pose record to a camera pose model.

    Arguments
    ---------
    camera_pose_record: Camera pose ORM record.

    Returns
    -------
    Mapped CameraPose domain model.
    """
    return models.CameraPose(
        camera_id=camera_pose_record.camera_id,
        location=camera_pose_record.location,
        srid=camera_pose_record.srid,
        yaw=camera_pose_record.yaw,
        pitch=camera_pose_record.pitch,
        roll=camera_pose_record.roll,
    )


@to_model.register
def _(camera_footprint_record: orm.CameraFootprintRecord) -> models.CameraFootprint:
    """
    Convert a camera footprint record to a camera footprint model.

    Arguments
    ---------
    camera_footprint_record: Camera footprint ORM record.

    Returns
    -------
    Mapped CameraFootprint domain model.
    """
    return models.CameraFootprint(
        camera_id=camera_footprint_record.camera_id,
        coordinates=camera_footprint_record.polygon,
        srid=camera_footprint_record.srid,
    )
