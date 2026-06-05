"""Unit tests for sealoc.models.Camera."""

from __future__ import annotations

from sealoc.models import (
    Camera,
    CameraCalibration,
    CameraFootprint,
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

_POSE = CameraPose(
    camera_id=1,
    location=(10.0, 63.0, 5.0),
    srid=_WGS84,
    yaw=0.0,
    pitch=0.0,
    roll=0.0,
)

_FOOTPRINT = CameraFootprint(
    camera_id=1,
    coordinates=[
        (9.999, 62.999, 0.0),
        (10.001, 62.999, 0.0),
        (10.001, 63.001, 0.0),
        (9.999, 63.001, 0.0),
    ],
    srid=_WGS84,
)


def _make_camera(
    camera_id: int = 1,
    master_camera: Camera | None = None,
    pose: CameraPose | None = None,
    footprint: CameraFootprint | None = None,
) -> Camera:
    return Camera(
        id=camera_id,
        label=f"camera_{camera_id:04d}",
        image_label=f"image_{camera_id:04d}",
        camera_sensor=_SENSOR,
        master_camera=master_camera,
        camera_pose=pose,
        camera_footprint=footprint,
    )


def test_camera_without_pose_has_no_pose() -> None:
    """has_pose() returns False and get_pose() returns None when no pose is set."""
    camera = _make_camera()
    assert camera.has_pose() is False
    assert camera.get_pose() is None


def test_camera_with_pose_has_pose() -> None:
    """has_pose() returns True and get_pose() returns the pose when one is set."""
    camera = _make_camera(pose=_POSE)
    assert camera.has_pose() is True
    assert camera.get_pose() is _POSE


def test_camera_without_footprint_has_no_footprint() -> None:
    """has_footprint() returns False and get_footprint() returns None when no footprint is set."""
    camera = _make_camera()
    assert camera.has_footprint() is False
    assert camera.get_footprint() is None


def test_camera_with_footprint_has_footprint() -> None:
    """has_footprint() returns True and get_footprint() returns the footprint when one is set."""
    camera = _make_camera(footprint=_FOOTPRINT)
    assert camera.has_footprint() is True
    assert camera.get_footprint() is _FOOTPRINT


def test_camera_without_master_is_master() -> None:
    """A camera without a master_camera is a master."""
    camera = _make_camera()
    assert camera.is_master is True
    assert camera.is_slave is False


def test_camera_with_master_is_slave() -> None:
    """A camera with a master_camera is a slave."""
    master = _make_camera(camera_id=1)
    slave = _make_camera(camera_id=2, master_camera=master)
    assert slave.is_slave is True
    assert slave.is_master is False
    assert slave.master_camera is master


def test_camera_sensor_accessible_via_sensor_property() -> None:
    """camera.sensor returns the camera_sensor."""
    camera = _make_camera()
    assert camera.sensor is _SENSOR
