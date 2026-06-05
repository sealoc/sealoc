"""
Module for calculating metrics based on camera poses.
"""

import numpy as np
import shapely  # type: ignore[import-untyped]
import shapely.ops  # type: ignore[import-untyped]

import sealoc.transforms as tfs

from sealoc.models import CameraPose


def calculate_pose_distance(
    pose1: CameraPose,
    pose2: CameraPose,
) -> float:
    """
    Calculate the distance between two camera poses in meters.

    Arguments
    ---------
    pose1: First camera pose.
    pose2: Second camera pose.

    Returns
    -------
    Distance between the two poses in meters.
    """
    crs_to: tfs.CRS = tfs.estimate_utm_crs([pose1.shape])

    transformer1: tfs.Transformer = tfs.Transformer.from_crs(
        crs_from=pose1.crs,
        crs_to=crs_to,
        always_xy=True,
    )
    transformer2: tfs.Transformer = tfs.Transformer.from_crs(
        crs_from=pose2.crs,
        crs_to=crs_to,
        always_xy=True,
    )

    shape1: shapely.Point = shapely.ops.transform(transformer1.transform, pose1.shape)
    shape2: shapely.Point = shapely.ops.transform(transformer2.transform, pose2.shape)

    return _calculate_point_distance_3d(shape1, shape2)


def calculate_point_distance(point1: shapely.Point, point2: shapely.Point) -> float:
    """
    Calculate the distance between two shapely points.

    Arguments
    ---------
    point1: First point.
    point2: Second point.

    Returns
    -------
    Euclidean distance between the two points.
    """
    array1: np.ndarray = np.array(point1.coords).squeeze()
    array2: np.ndarray = np.array(point2.coords).squeeze()
    return float(np.linalg.norm(array1 - array2))


def _calculate_point_distance_2d(point1: shapely.Point, point2: shapely.Point) -> float:
    """Calculates the 2D Euclidean distance between two points."""
    return point1.distance(point2)


def _calculate_point_distance_3d(point1: shapely.Point, point2: shapely.Point) -> float:
    """Calculates the 3D Euclidean distance between two points."""
    array1: np.ndarray = np.array(point1.coords).squeeze()
    array2: np.ndarray = np.array(point2.coords).squeeze()
    return float(np.linalg.norm(array1 - array2))
