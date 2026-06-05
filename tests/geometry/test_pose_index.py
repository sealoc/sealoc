"""Unit tests for sealoc.geometry.pose_index."""

from __future__ import annotations

import pytest
import shapely  # type: ignore[import-untyped]

from sealoc.geometry import (
    CameraPoseIndex,
    create_camera_pose_index,
)
from sealoc.geometry.types import CameraPoseLink
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


@pytest.fixture
def index() -> CameraPoseIndex:
    # A and B are ~111 m apart; FAR is ~111 km from A.
    return create_camera_pose_index(
        [
            _pose(1, lon=10.0, lat=63.0),
            _pose(2, lon=10.0, lat=63.001),
            _pose(3, lon=10.0, lat=64.0),
        ]
    )


def test_create_camera_pose_index_empty_raises() -> None:
    """Empty pose list raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        create_camera_pose_index([])


def test_create_camera_pose_index_mixed_crs_raises() -> None:
    """Poses with different SRIDs raise ValueError."""
    pose_wgs84: CameraPose = _pose(1, lon=10.0, lat=63.0)
    pose_utm: CameraPose = CameraPose(
        camera_id=2,
        location=(500000.0, 6990000.0, 0.0),
        srid=32632,
        yaw=0.0,
        pitch=0.0,
        roll=0.0,
    )
    with pytest.raises(ValueError, match="SRID"):
        create_camera_pose_index([pose_wgs84, pose_utm])


def test_create_camera_pose_index_returns_index() -> None:
    """Returns a CameraPoseIndex instance."""
    assert isinstance(create_camera_pose_index([_pose(1, 10.0, 63.0)]), CameraPoseIndex)


def test_create_camera_pose_index_stores_all_poses() -> None:
    """All provided poses are stored in the index."""
    index: CameraPoseIndex = create_camera_pose_index(
        [_pose(1, 10.0, 63.0), _pose(2, 10.0, 63.001)]
    )
    assert len(index.database_poses) == 2


def test_pose_index_str_contains_count(index: CameraPoseIndex) -> None:
    """String representation includes the number of poses."""
    assert "3" in str(index)


def test_pose_index_source_crs_is_geographic(index: CameraPoseIndex) -> None:
    """Source CRS is geographic (not projected)."""
    assert index.source_crs.is_geographic


def test_pose_index_target_crs_is_projected(index: CameraPoseIndex) -> None:
    """Target CRS is a projected (UTM) coordinate system."""
    assert index.target_crs.is_projected


def test_pose_index_database_points_count(index: CameraPoseIndex) -> None:
    """database_points returns one projected point per indexed pose."""
    points: list[shapely.Point] = index.database_points
    assert len(points) == 3
    assert all(isinstance(point, shapely.Point) for point in points)


def test_pose_index_has_pose_known_id(index: CameraPoseIndex) -> None:
    """has_pose returns True for a camera_id present in the index."""
    assert index.has_pose(1) is True


def test_pose_index_has_pose_unknown_id(index: CameraPoseIndex) -> None:
    """has_pose returns False for a camera_id not in the index."""
    assert index.has_pose(999) is False


def test_pose_index_search_finds_nearby_poses(index: CameraPoseIndex) -> None:
    """search returns poses within the distance threshold."""
    query: CameraPose = _pose(99, lon=10.0, lat=63.0)
    results: list[CameraPose] = index.search(query, max_distance=500.0)
    result_ids: set[int] = {pose.camera_id for pose in results}
    assert 1 in result_ids
    assert 2 in result_ids


def test_pose_index_search_excludes_distant_poses(index: CameraPoseIndex) -> None:
    """search excludes poses beyond the distance threshold."""
    query: CameraPose = _pose(99, lon=10.0, lat=63.0)
    results: list[CameraPose] = index.search(query, max_distance=500.0)
    result_ids: set[int] = {pose.camera_id for pose in results}
    assert 3 not in result_ids


def test_pose_index_search_links_returns_pose_links(index: CameraPoseIndex) -> None:
    """search_links returns CameraPoseLink instances."""
    query: CameraPose = _pose(99, lon=10.0, lat=63.0)
    links: list[CameraPoseLink] = index.search_links(query, max_distance=500.0)
    assert all(isinstance(link, CameraPoseLink) for link in links)


def test_pose_index_search_links_distance_non_negative(index: CameraPoseIndex) -> None:
    """search_links populates a non-negative distance_meters on each link."""
    query: CameraPose = _pose(99, lon=10.0, lat=63.001)
    links: list[CameraPoseLink] = index.search_links(query, max_distance=500.0)
    assert all(link.distance_meters >= 0.0 for link in links)


def test_pose_index_search_links_query_pose_set(index: CameraPoseIndex) -> None:
    """search_links stores the query pose on each returned link."""
    query: CameraPose = _pose(99, lon=10.0, lat=63.0)
    links: list[CameraPoseLink] = index.search_links(query, max_distance=500.0)
    assert all(link.query_pose == query for link in links)


def test_pose_link_query_camera_id() -> None:
    """query_camera_id returns the camera id of the query pose."""
    query: CameraPose = _pose(10, lon=10.0, lat=63.0)
    database: CameraPose = _pose(20, lon=10.0, lat=63.001)
    link: CameraPoseLink = CameraPoseLink(
        query_pose=query, database_pose=database, distance_meters=111.0
    )
    assert link.query_camera_id == 10


def test_pose_link_database_camera_id() -> None:
    """database_camera_id returns the camera id of the database pose."""
    query: CameraPose = _pose(10, lon=10.0, lat=63.0)
    database: CameraPose = _pose(20, lon=10.0, lat=63.001)
    link: CameraPoseLink = CameraPoseLink(
        query_pose=query, database_pose=database, distance_meters=111.0
    )
    assert link.database_camera_id == 20
