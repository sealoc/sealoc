"""Unit tests for sealoc.geometry.footprint_index."""

from __future__ import annotations

import pytest
import shapely  # type: ignore[import-untyped]

from sealoc.geometry import (
    CameraFootprintIndex,
    create_camera_footprint_index,
)
from sealoc.geometry.types import CameraFootprintLink
from sealoc.models import CameraFootprint

_WGS84: int = 4326

# Footprint A: lon [9.999, 10.001], lat [62.999, 63.001]
# Footprint B: lon [10.0, 10.002], lat [63.0, 63.002] — partially overlaps A
# Footprint FAR: does not overlap with A or B
_FOOTPRINT_A = CameraFootprint(
    camera_id=1,
    coordinates=[
        (9.999, 62.999, 0.0),
        (10.001, 62.999, 0.0),
        (10.001, 63.001, 0.0),
        (9.999, 63.001, 0.0),
    ],
    srid=_WGS84,
)
_FOOTPRINT_B = CameraFootprint(
    camera_id=2,
    coordinates=[
        (10.0, 63.0, 0.0),
        (10.002, 63.0, 0.0),
        (10.002, 63.002, 0.0),
        (10.0, 63.002, 0.0),
    ],
    srid=_WGS84,
)
_FOOTPRINT_FAR = CameraFootprint(
    camera_id=3,
    coordinates=[
        (10.9, 63.9, 0.0),
        (10.902, 63.9, 0.0),
        (10.902, 63.902, 0.0),
        (10.9, 63.902, 0.0),
    ],
    srid=_WGS84,
)


@pytest.fixture
def index() -> CameraFootprintIndex:
    return create_camera_footprint_index([_FOOTPRINT_A, _FOOTPRINT_B, _FOOTPRINT_FAR])


def test_create_camera_footprint_index_empty_raises() -> None:
    """Empty footprint list raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        create_camera_footprint_index([])


def test_create_camera_footprint_index_mixed_crs_raises() -> None:
    """Footprints with different SRIDs raise ValueError."""
    footprint_utm: CameraFootprint = CameraFootprint(
        camera_id=99,
        coordinates=[
            (500000.0, 6990000.0, 0.0),
            (500100.0, 6990000.0, 0.0),
            (500100.0, 6990100.0, 0.0),
            (500000.0, 6990100.0, 0.0),
        ],
        srid=32632,
    )
    with pytest.raises(ValueError, match="SRID"):
        create_camera_footprint_index([_FOOTPRINT_A, footprint_utm])


def test_create_camera_footprint_index_returns_index() -> None:
    """Returns a CameraFootprintIndex instance."""
    assert isinstance(
        create_camera_footprint_index([_FOOTPRINT_A, _FOOTPRINT_B]),
        CameraFootprintIndex,
    )


def test_create_camera_footprint_index_stores_all_footprints() -> None:
    """All provided footprints are stored in the index."""
    index: CameraFootprintIndex = create_camera_footprint_index(
        [_FOOTPRINT_A, _FOOTPRINT_B]
    )
    assert len(index.database_footprints) == 2


def test_footprint_index_str_contains_count(index: CameraFootprintIndex) -> None:
    """String representation includes the number of footprints."""
    assert "3" in str(index)


def test_footprint_index_source_crs_is_geographic(index: CameraFootprintIndex) -> None:
    """Source CRS is geographic (not projected)."""
    assert index.source_crs.is_geographic


def test_footprint_index_target_crs_is_projected(index: CameraFootprintIndex) -> None:
    """Target CRS is a projected (UTM) coordinate system."""
    assert index.target_crs.is_projected


def test_footprint_index_database_polygons_count(index: CameraFootprintIndex) -> None:
    """database_polygons returns one projected polygon per indexed footprint."""
    polygons: list[shapely.Polygon] = index.database_polygons
    assert len(polygons) == 3
    assert all(isinstance(polygon, shapely.Polygon) for polygon in polygons)


def test_footprint_index_search_finds_overlapping(index: CameraFootprintIndex) -> None:
    """search returns footprints that intersect the query footprint."""
    results: list[CameraFootprint] = index.search(_FOOTPRINT_A)
    result_ids: set[int] = {footprint.camera_id for footprint in results}
    assert 1 in result_ids
    assert 2 in result_ids


def test_footprint_index_search_excludes_non_overlapping(
    index: CameraFootprintIndex,
) -> None:
    """search excludes footprints that do not intersect the query footprint."""
    results: list[CameraFootprint] = index.search(_FOOTPRINT_A)
    result_ids: set[int] = {footprint.camera_id for footprint in results}
    assert 3 not in result_ids


def test_footprint_index_search_links_returns_footprint_links(
    index: CameraFootprintIndex,
) -> None:
    """search_links returns CameraFootprintLink instances."""
    links: list[CameraFootprintLink] = index.search_links(_FOOTPRINT_A)
    assert all(isinstance(link, CameraFootprintLink) for link in links)


def test_footprint_index_search_links_iou_in_unit_interval(
    index: CameraFootprintIndex,
) -> None:
    """search_links populates a footprint_iou in [0, 1] for each link."""
    links: list[CameraFootprintLink] = index.search_links(_FOOTPRINT_A)
    assert all(0.0 <= link.footprint_iou <= 1.0 for link in links)


def test_footprint_index_search_links_areas_are_positive(
    index: CameraFootprintIndex,
) -> None:
    """search_links populates positive footprint areas on each link."""
    links: list[CameraFootprintLink] = index.search_links(_FOOTPRINT_A)
    assert all(link.query_footprint_area > 0.0 for link in links)
    assert all(link.database_footprint_area > 0.0 for link in links)


def test_footprint_index_search_links_query_footprint_set(
    index: CameraFootprintIndex,
) -> None:
    """search_links stores the query footprint on each returned link."""
    links: list[CameraFootprintLink] = index.search_links(_FOOTPRINT_A)
    assert all(link.query_footprint == _FOOTPRINT_A for link in links)
