"""Unit tests for sealoc.models.CameraBundle."""

from __future__ import annotations

from sealoc.models import (
    Camera,
    CameraBundle,
    CameraCalibration,
    CameraGroup,
    CameraSensor,
)


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


def _make_camera(camera_id: int) -> Camera:
    return Camera(
        id=camera_id,
        label=f"camera_{camera_id:04d}",
        image_label=f"image_{camera_id:04d}",
        camera_sensor=_SENSOR,
    )


def _make_group(group_id: int, camera_ids: list[int]) -> CameraGroup:
    group = CameraGroup(id=group_id, label=f"dive_{group_id:02d}")
    for camera_id in camera_ids:
        group.add_camera(_make_camera(camera_id))
    group.add_sensor(_SENSOR)
    return group


def test_cameras_returns_flat_list_across_groups() -> None:
    """cameras property returns all cameras from all groups as a flat list."""
    bundle = CameraBundle(id=1, label="survey_2023")
    bundle.add_group(_make_group(group_id=1, camera_ids=[1, 2]))
    bundle.add_group(_make_group(group_id=2, camera_ids=[3, 4]))

    assert len(bundle.cameras) == 4


def test_camera_sensors_returns_flat_list_across_groups() -> None:
    """camera_sensors property returns all sensors from all groups as a flat list."""
    bundle = CameraBundle(id=1, label="survey_2023")
    bundle.add_group(_make_group(group_id=1, camera_ids=[1]))
    bundle.add_group(_make_group(group_id=2, camera_ids=[2]))

    assert len(bundle.camera_sensors) == 2


def test_groups_returns_camera_groups() -> None:
    """groups property returns the set of camera groups in the bundle."""
    group_a = _make_group(group_id=1, camera_ids=[1])
    group_b = _make_group(group_id=2, camera_ids=[2])

    bundle = CameraBundle(id=1, label="survey_2023")
    bundle.add_group(group_a)
    bundle.add_group(group_b)

    assert group_a in bundle.groups
    assert group_b in bundle.groups


def test_add_group_links_bundle_to_group() -> None:
    """add_group sets group.camera_bundle to the bundle."""
    bundle = CameraBundle(id=1, label="survey_2023")
    group = _make_group(group_id=1, camera_ids=[1])
    bundle.add_group(group)

    assert group.camera_bundle is bundle
