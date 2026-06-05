"""Module for a camera footprint index."""

import dataclasses

import numpy as np
import shapely  # type: ignore[import-untyped]
import shapely.ops  # type: ignore[import-untyped]

import sealoc.transforms as tfs

from sealoc.models import CameraFootprint

from .footprint_metrics import calculate_footprint_area
from .footprint_metrics import calculate_footprint_iou
from .types import CameraFootprintLink


@dataclasses.dataclass(frozen=True)
class CameraFootprintIndex:
    """
    Spatial index for finding cameras with overlapping footprints.

    Attributes
    ----------
    database_footprints: Footprints stored in the index.
    database_transformer: Transformer used to project footprints into the index CRS.
    database_tree: STRtree of projected footprint polygons.
    """

    database_footprints: list[CameraFootprint]
    database_transformer: tfs.Transformer
    database_tree: shapely.STRtree

    def __str__(self) -> str:
        """Returns a string representation of the camera footprint index."""
        attributes: str = f"footprints={len(self.database_footprints)}"
        return f"{self.__class__.__name__}({attributes})"

    @property
    def source_crs(self) -> tfs.CRS:
        """
        Source CRS of the database transformer.

        Returns
        -------
        Source CRS used when projecting database footprints.
        """
        crs = self.database_transformer.source_crs
        assert crs is not None
        return crs

    @property
    def target_crs(self) -> tfs.CRS:
        """
        Target CRS of the database transformer.

        Returns
        -------
        Target CRS (UTM) used for spatial querying.
        """
        crs = self.database_transformer.target_crs
        assert crs is not None
        return crs

    @property
    def database_polygons(self) -> list[shapely.Polygon]:
        """
        Polygons stored in the database tree.

        Returns
        -------
        List of projected footprint polygons in the index.
        """
        return list(self.database_tree.geometries)

    def search(
        self,
        query_footprint: CameraFootprint,
    ) -> list[CameraFootprint]:
        """
        Search for database cameras whose footprint intersects the query footprint.

        Arguments
        ---------
        query_footprint: Footprint to search against the index.

        Returns
        -------
        Database footprints that intersect the query footprint.
        """
        query_transformer: tfs.Transformer = tfs.Transformer.from_crs(
            query_footprint.crs,
            self.target_crs,
            always_xy=True,
        )

        query_polygon: shapely.Polygon = shapely.ops.transform(
            query_transformer.transform, query_footprint.shape
        )

        indices: np.ndarray = self.database_tree.query(
            query_polygon, predicate="intersects"
        )
        return [self.database_footprints[index] for index in indices]

    def search_links(
        self,
        query_footprint: CameraFootprint,
    ) -> list[CameraFootprintLink]:
        """
        Return CameraFootprintLinks for all database footprints overlapping the query.

        Arguments
        ---------
        query_footprint: Footprint to search against the index.

        Returns
        -------
        Links between the query footprint and each overlapping database footprint.
        """
        overlapping_footprints: list[CameraFootprint] = self.search(query_footprint)
        return [
            CameraFootprintLink(
                query_footprint=query_footprint,
                database_footprint=database_footprint,
                query_footprint_area=calculate_footprint_area(query_footprint),
                database_footprint_area=calculate_footprint_area(database_footprint),
                footprint_iou=calculate_footprint_iou(
                    query_footprint, database_footprint
                ),
            )
            for database_footprint in overlapping_footprints
        ]


def create_camera_footprint_index(
    camera_footprints: list[CameraFootprint],
) -> CameraFootprintIndex:
    """
    Create a camera footprint index from a collection of camera footprints.

    Arguments
    ---------
    camera_footprints: Footprints to index. Must be non-empty and all in the same CRS.

    Returns
    -------
    CameraFootprintIndex built from the given footprints.
    """
    if len(camera_footprints) == 0:
        raise ValueError("camera_footprints must not be empty.")

    srids: set[int] = {footprint.srid for footprint in camera_footprints}
    if len(srids) > 1:
        raise ValueError(f"All footprints must share the same CRS, got SRIDs: {srids}.")

    polygons: list[shapely.Polygon] = [
        footprint.shape for footprint in camera_footprints
    ]
    centroids: list[shapely.Point] = [
        footprint.centroid for footprint in camera_footprints
    ]

    crs_from: tfs.CRS = camera_footprints[0].crs
    crs_to: tfs.CRS = tfs.estimate_utm_crs(centroids)

    transformer: tfs.Transformer = tfs.Transformer.from_crs(
        crs_from,
        crs_to,
        always_xy=True,
    )

    transformed_polygons: list[shapely.Polygon] = [
        shapely.ops.transform(transformer.transform, polygon) for polygon in polygons
    ]
    tree: shapely.STRtree = shapely.STRtree(transformed_polygons)

    return CameraFootprintIndex(camera_footprints, transformer, tree)
