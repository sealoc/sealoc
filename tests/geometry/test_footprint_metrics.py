"""Unit tests for sealoc.geometry.footprint_metrics."""

from __future__ import annotations


from sealoc.geometry import (
    calculate_footprint_area,
    calculate_footprint_intersection_area,
    calculate_footprint_iou,
    calculate_footprint_union_area,
)
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


def test_calculate_footprint_area_positive() -> None:
    """Area of a non-degenerate footprint is positive."""
    assert calculate_footprint_area(_FOOTPRINT_A) > 0.0


def test_calculate_footprint_area_larger_footprint() -> None:
    """A footprint with double the side length has a larger area."""
    small: CameraFootprint = CameraFootprint(
        camera_id=10,
        coordinates=[
            (10.0, 63.0, 0.0),
            (10.001, 63.0, 0.0),
            (10.001, 63.001, 0.0),
            (10.0, 63.001, 0.0),
        ],
        srid=_WGS84,
    )
    large: CameraFootprint = CameraFootprint(
        camera_id=11,
        coordinates=[
            (10.0, 63.0, 0.0),
            (10.002, 63.0, 0.0),
            (10.002, 63.002, 0.0),
            (10.0, 63.002, 0.0),
        ],
        srid=_WGS84,
    )
    assert calculate_footprint_area(large) > calculate_footprint_area(small)


def test_calculate_footprint_intersection_area_overlapping() -> None:
    """Partially overlapping footprints have a positive intersection area."""
    assert calculate_footprint_intersection_area(_FOOTPRINT_A, _FOOTPRINT_B) > 0.0


def test_calculate_footprint_intersection_area_non_overlapping() -> None:
    """Spatially separated footprints have zero intersection area."""
    assert calculate_footprint_intersection_area(_FOOTPRINT_A, _FOOTPRINT_FAR) == 0.0


def test_calculate_footprint_intersection_area_smaller_than_each() -> None:
    """Intersection area is smaller than the area of either footprint."""
    intersection: float = calculate_footprint_intersection_area(
        _FOOTPRINT_A, _FOOTPRINT_B
    )
    assert intersection < calculate_footprint_area(_FOOTPRINT_A)
    assert intersection < calculate_footprint_area(_FOOTPRINT_B)


def test_calculate_footprint_union_area_overlapping() -> None:
    """Union of overlapping footprints is positive."""
    assert calculate_footprint_union_area(_FOOTPRINT_A, _FOOTPRINT_B) > 0.0


def test_calculate_footprint_union_area_non_overlapping() -> None:
    """Union of non-overlapping footprints returns zero (overlaps predicate returns False)."""
    assert calculate_footprint_union_area(_FOOTPRINT_A, _FOOTPRINT_FAR) == 0.0


def test_calculate_footprint_union_area_larger_than_each() -> None:
    """Union of overlapping footprints is larger than either individual footprint."""
    union: float = calculate_footprint_union_area(_FOOTPRINT_A, _FOOTPRINT_B)
    assert union > calculate_footprint_area(_FOOTPRINT_A)
    assert union > calculate_footprint_area(_FOOTPRINT_B)


def test_calculate_footprint_iou_non_overlapping_is_zero() -> None:
    """IoU is zero for spatially separated footprints."""
    assert calculate_footprint_iou(_FOOTPRINT_A, _FOOTPRINT_FAR) == 0.0


def test_calculate_footprint_iou_overlapping_in_unit_interval() -> None:
    """IoU is in (0, 1) for partially overlapping footprints."""
    iou: float = calculate_footprint_iou(_FOOTPRINT_A, _FOOTPRINT_B)
    assert 0.0 < iou < 1.0
