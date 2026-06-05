"""
Module for calculating metrics based on camera footprints.
"""

import shapely  # type: ignore[import-untyped]
import shapely.ops  # type: ignore[import-untyped]

import sealoc.transforms as tfs

from sealoc.models import CameraFootprint


def calculate_footprint_area(footprint: CameraFootprint) -> float:
    """
    Calculate the area of a footprint in square meters.

    Arguments
    ---------
    footprint: Camera footprint to measure.

    Returns
    -------
    Footprint area in square meters.
    """
    return _calculate_polygon_area(footprint.shape, footprint.crs)


def calculate_footprint_intersection_area(
    footprint1: CameraFootprint,
    footprint2: CameraFootprint,
) -> float:
    """
    Calculate the area of the intersection between two camera footprints.

    Arguments
    ---------
    footprint1: First camera footprint.
    footprint2: Second camera footprint.

    Returns
    -------
    Intersection area in square meters.
    """
    crs_equal_area: tfs.CRS = tfs.CRS("EPSG:6933")

    transformer1: tfs.Transformer = tfs.Transformer.from_crs(
        footprint1.crs, crs_equal_area, always_xy=True
    )
    transformer2: tfs.Transformer = tfs.Transformer.from_crs(
        footprint2.crs, crs_equal_area, always_xy=True
    )

    polygon1: shapely.Polygon = shapely.ops.transform(
        transformer1.transform, footprint1.shape
    )
    polygon2: shapely.Polygon = shapely.ops.transform(
        transformer2.transform, footprint2.shape
    )

    if not polygon1.overlaps(polygon2):
        return 0.0

    return polygon1.intersection(polygon2).area


def calculate_footprint_union_area(
    footprint1: CameraFootprint,
    footprint2: CameraFootprint,
) -> float:
    """
    Calculate the area of the union between two camera footprints.

    Arguments
    ---------
    footprint1: First camera footprint.
    footprint2: Second camera footprint.

    Returns
    -------
    Union area in square meters.
    """
    crs_equal_area: tfs.CRS = tfs.CRS("EPSG:6933")

    transformer1: tfs.Transformer = tfs.Transformer.from_crs(
        footprint1.crs, crs_equal_area, always_xy=True
    )
    transformer2: tfs.Transformer = tfs.Transformer.from_crs(
        footprint2.crs, crs_equal_area, always_xy=True
    )

    polygon1: shapely.Polygon = shapely.ops.transform(
        transformer1.transform, footprint1.shape
    )
    polygon2: shapely.Polygon = shapely.ops.transform(
        transformer2.transform, footprint2.shape
    )

    if not polygon1.overlaps(polygon2):
        return 0.0

    return polygon1.union(polygon2).area


def calculate_footprint_iou(
    footprint1: CameraFootprint,
    footprint2: CameraFootprint,
) -> float:
    """
    Calculate the intersection over union (IoU) for two camera footprints.

    Arguments
    ---------
    footprint1: First camera footprint.
    footprint2: Second camera footprint.

    Returns
    -------
    IoU as a ratio in [0, 1].
    """
    intersection_area: float = calculate_footprint_intersection_area(
        footprint1, footprint2
    )
    union_area: float = calculate_footprint_union_area(footprint1, footprint2)

    if union_area == 0.0:
        return 0.0

    return intersection_area / union_area


def _calculate_polygon_area(polygon: shapely.Polygon, crs_from: tfs.CRS) -> float:
    """Calculates the area of a polygon in square meters using an equal-area projection."""
    crs_equal_area: tfs.CRS = tfs.CRS("EPSG:6933")

    transformer: tfs.Transformer = tfs.Transformer.from_crs(
        crs_from,
        crs_equal_area,
        always_xy=True,
    )

    equal_area_polygon: shapely.Polygon = shapely.ops.transform(
        transformer.transform, polygon
    )
    return equal_area_polygon.area
