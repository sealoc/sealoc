"""Module for common spatial functionality."""

import shapely  # type: ignore[import-untyped]

from pyproj import (
    CRS as CRS,
    Transformer as Transformer,
)
from scipy.spatial.transform import (  # type: ignore[import-untyped]
    RigidTransform as RigidTransform,
    Rotation as Rotation,
)

from .constants import (
    LATITUDE_LOWER_DEG,
    LATITUDE_UPPER_DEG,
    LONGITUDE_LOWER_DEG,
    LONGITUDE_UPPER_DEG,
)


def estimate_utm_crs(points: list[shapely.Point]) -> CRS:
    """
    Estimate the UTM CRS from a collection of WGS84 points.

    Arguments
    ---------
    points: WGS84 points (longitude, latitude) to estimate the UTM zone from.

    Returns
    -------
    UTM CRS for the zone covering the centroid of the input points.
    """
    for point in points:
        assert (
            LONGITUDE_LOWER_DEG < point.x < LONGITUDE_UPPER_DEG
        ), f"invalid longitude: {point}"
        assert (
            LATITUDE_LOWER_DEG < point.y < LATITUDE_UPPER_DEG
        ), f"invalid latitude: {point}"

    lons: list[float] = [point.x for point in points]
    lats: list[float] = [point.y for point in points]

    # Calculate
    center_lon: float = sum(lons) / len(lons)
    center_lat: float = sum(lats) / len(lats)

    zone_number: int = round((center_lon + 180) / 6)
    is_northern: bool = center_lat >= 0

    # Create CRS for the corresponding UTM zone
    if is_northern:
        crs: CRS = CRS.from_epsg(32600 + zone_number)  # Northern hemisphere
    else:
        crs = CRS.from_epsg(32700 + zone_number)  # Southern hemisphere

    return crs
