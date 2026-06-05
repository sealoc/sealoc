"""Unit tests for sealoc.geometry.pose_metrics."""

from __future__ import annotations

import pytest
import shapely  # type: ignore[import-untyped]

from sealoc.geometry import (
    calculate_point_distance,
    calculate_pose_distance,
)
from sealoc.models import CameraPose

_WGS84: int = 4326


def _pose(camera_id: int, lon: float, lat: float, alt: float = 0.0) -> CameraPose:
    return CameraPose(
        camera_id=camera_id,
        location=(lon, lat, alt),
        srid=_WGS84,
        yaw=0.0,
        pitch=0.0,
        roll=0.0,
    )


def test_calculate_point_distance_coincident_points() -> None:
    """Distance between a point and itself is zero."""
    point: shapely.Point = shapely.Point(0.0, 0.0)
    assert calculate_point_distance(point, point) == 0.0


def test_calculate_point_distance_2d_known_value() -> None:
    """Distance between (0, 0) and (3, 4) is 5."""
    assert calculate_point_distance(
        shapely.Point(0.0, 0.0), shapely.Point(3.0, 4.0)
    ) == pytest.approx(5.0)


def test_calculate_point_distance_3d_known_value() -> None:
    """3D distance uses all three coordinates."""
    assert calculate_point_distance(
        shapely.Point(0.0, 0.0, 0.0), shapely.Point(1.0, 2.0, 2.0)
    ) == pytest.approx(3.0)


def test_calculate_pose_distance_same_pose() -> None:
    """Distance from a pose to itself is zero."""
    pose: CameraPose = _pose(1, lon=10.0, lat=63.0)
    assert calculate_pose_distance(pose, pose) == pytest.approx(0.0, abs=1e-6)


def test_calculate_pose_distance_nearby_poses() -> None:
    """Two poses 0.001 degrees of latitude apart are approximately 111 m from each other."""
    pose_a: CameraPose = _pose(1, lon=10.0, lat=63.0)
    pose_b: CameraPose = _pose(2, lon=10.0, lat=63.001)
    distance: float = calculate_pose_distance(pose_a, pose_b)
    assert 100.0 < distance < 120.0


def test_calculate_pose_distance_symmetric() -> None:
    """Distance from A to B equals distance from B to A."""
    pose_a: CameraPose = _pose(1, lon=10.0, lat=63.0)
    pose_b: CameraPose = _pose(2, lon=10.0, lat=63.001)
    assert calculate_pose_distance(pose_a, pose_b) == pytest.approx(
        calculate_pose_distance(pose_b, pose_a)
    )
