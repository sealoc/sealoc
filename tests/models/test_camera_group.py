"""Unit tests for sealoc.models.CameraGroup."""

from __future__ import annotations

from sealoc.models import (
    Camera,
    CameraCalibration,
    CameraFootprint,
    CameraGroup,
    CameraPose,
    CameraSensor,
)


_WGS84: int = 4326

_CALIBRATION = CameraCalibration(
    id=1,
    width=1920,
    height=1080,
    fx=800.0,
    fy=800.0,
    cx=960.0,
    cy=540.0,
    k1=0.0,
    k2=0.0,
    k3=0.0,
    p1=0.0,
    p2=0.0,
)

_SENSOR = CameraSensor(
    id=1,
    label="left",
    width=1920,
    height=1080,
    calibration=_CALIBRATION,
)


def _make_camera(
    camera_id: int,
    pose: CameraPose | None = None,
    footprint: CameraFootprint | None = None,
) -> Camera:
    return Camera(
        id=camera_id,
        label=f"camera_{camera_id:04d}",
        image_label=f"image_{camera_id:04d}",
        camera_sensor=_SENSOR,
        camera_pose=pose,
        camera_footprint=footprint,
    )


def _make_pose(camera_id: int) -> CameraPose:
    return CameraPose(
        camera_id=camera_id,
        location=(10.0, 63.0, 5.0),
        srid=_WGS84,
        yaw=0.0,
        pitch=0.0,
        roll=0.0,
    )


def _make_footprint(camera_id: int) -> CameraFootprint:
    return CameraFootprint(
        camera_id=camera_id,
        coordinates=[
            (9.999, 62.999, 0.0),
            (10.001, 62.999, 0.0),
            (10.001, 63.001, 0.0),
            (9.999, 63.001, 0.0),
        ],
        srid=_WGS84,
    )


def test_camera_poses_returns_only_cameras_with_poses() -> None:
    """camera_poses includes only cameras that have a pose attached."""
    camera_with_pose = _make_camera(1, pose=_make_pose(1))
    camera_without_pose = _make_camera(2)

    group = CameraGroup(id=1, label="dive_01")
    group.add_camera(camera_with_pose)
    group.add_camera(camera_without_pose)

    poses = group.camera_poses
    assert len(poses) == 1
    assert poses[0].camera_id == 1


def test_camera_poses_empty_when_no_cameras_have_poses() -> None:
    """camera_poses is empty when no camera in the group has a pose."""
    group = CameraGroup(id=1, label="dive_01")
    group.add_camera(_make_camera(1))
    group.add_camera(_make_camera(2))

    assert group.camera_poses == []


def test_camera_footprints_returns_only_cameras_with_footprints() -> None:
    """camera_footprints includes only cameras that have a footprint attached."""
    camera_with_footprint = _make_camera(1, footprint=_make_footprint(1))
    camera_without_footprint = _make_camera(2)

    group = CameraGroup(id=1, label="dive_01")
    group.add_camera(camera_with_footprint)
    group.add_camera(camera_without_footprint)

    footprints = group.camera_footprints
    assert len(footprints) == 1
    assert footprints[0].camera_id == 1


def test_camera_footprints_empty_when_no_cameras_have_footprints() -> None:
    """camera_footprints is empty when no camera in the group has a footprint."""
    group = CameraGroup(id=1, label="dive_01")
    group.add_camera(_make_camera(1))
    group.add_camera(_make_camera(2))

    assert group.camera_footprints == []


def test_add_camera_links_group_to_camera() -> None:
    """add_camera sets camera.camera_group to the group."""
    group = CameraGroup(id=1, label="dive_01")
    camera = _make_camera(1)
    group.add_camera(camera)

    assert camera in group.cameras
    assert camera.camera_group is group


def test_add_sensor_links_group_to_sensor() -> None:
    """add_sensor sets sensor.camera_group to the group."""
    group = CameraGroup(id=1, label="dive_01")
    group.add_sensor(_SENSOR)

    assert _SENSOR in group.camera_sensors
    assert _SENSOR.camera_group is group
