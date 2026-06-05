"""Module for a camera pose index."""

import dataclasses

import numpy as np
import shapely  # type: ignore[import-untyped]
import shapely.ops  # type: ignore[import-untyped]

import sealoc.transforms as tfs

from sealoc.models import CameraPose

from .pose_metrics import calculate_pose_distance
from .types import CameraPoseLink


@dataclasses.dataclass(frozen=True)
class CameraPoseIndex:
    """
    Spatial index for finding camera poses within a distance threshold.

    Attributes
    ----------
    database_poses: Poses stored in the index.
    database_transformer: Transformer used to project poses into the index CRS.
    database_tree: STRtree of projected pose points.
    """

    database_poses: list[CameraPose]
    database_transformer: tfs.Transformer
    database_tree: shapely.STRtree

    def __str__(self) -> str:
        """Returns a string representation of the camera pose index."""
        attributes: str = f"database_poses={len(self.database_poses)}"
        return f"{self.__class__.__name__}({attributes})"

    @property
    def source_crs(self) -> tfs.CRS:
        """
        Source CRS of the database transformer.

        Returns
        -------
        Source CRS used when projecting database poses.
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
        Target CRS (UTM) used for distance-based querying.
        """
        crs = self.database_transformer.target_crs
        assert crs is not None
        return crs

    @property
    def database_points(self) -> list[shapely.Point]:
        """
        Points stored in the database tree.

        Returns
        -------
        List of projected pose points in the index.
        """
        return list(self.database_tree.geometries)

    def has_pose(self, camera_id: int) -> bool:
        """
        Return True if there is a pose for the given camera id.

        Arguments
        ---------
        camera_id: Camera id to look up.

        Returns
        -------
        True if the index contains a pose for camera_id.
        """
        camera_ids: list[int] = [pose.camera_id for pose in self.database_poses]
        return camera_id in camera_ids

    def search(
        self,
        query_pose: CameraPose,
        max_distance: float,
    ) -> list[CameraPose]:
        """
        Return database poses within a distance threshold of the query pose.

        Arguments
        ---------
        query_pose: Pose of the query camera.
        max_distance: Maximum distance threshold in meters.

        Returns
        -------
        Database poses within max_distance meters of the query pose.
        """
        query_transformer: tfs.Transformer = tfs.Transformer.from_crs(
            query_pose.crs,
            self.target_crs,
            always_xy=True,
        )

        query_point: shapely.Point = shapely.ops.transform(
            query_transformer.transform, query_pose.shape
        )

        indices: np.ndarray = self.database_tree.query(
            query_point,
            predicate="dwithin",
            distance=max_distance,
        )
        return [self.database_poses[index] for index in indices]

    def search_links(
        self,
        query_pose: CameraPose,
        max_distance: float,
    ) -> list[CameraPoseLink]:
        """
        Return CameraPoseLinks for all database poses within the distance threshold.

        Arguments
        ---------
        query_pose: Pose of the query camera.
        max_distance: Maximum distance threshold in meters.

        Returns
        -------
        Links between the query pose and each proximate database pose.
        """
        proximate_poses: list[CameraPose] = self.search(query_pose, max_distance)
        return [
            CameraPoseLink(
                query_pose=query_pose,
                database_pose=database_pose,
                distance_meters=calculate_pose_distance(query_pose, database_pose),
            )
            for database_pose in proximate_poses
        ]


def create_camera_pose_index(
    camera_poses: list[CameraPose],
) -> CameraPoseIndex:
    """
    Create a pose index from a collection of camera poses.

    Arguments
    ---------
    camera_poses: Poses to index. Must be non-empty and all in the same CRS.

    Returns
    -------
    CameraPoseIndex built from the given poses.
    """
    if len(camera_poses) == 0:
        raise ValueError("camera_poses must not be empty.")

    srids: set[int] = {pose.srid for pose in camera_poses}
    if len(srids) > 1:
        raise ValueError(f"All poses must share the same CRS, got SRIDs: {srids}.")

    points: list[shapely.Point] = [camera_pose.shape for camera_pose in camera_poses]

    crs_from: tfs.CRS = camera_poses[0].crs
    crs_to: tfs.CRS = tfs.estimate_utm_crs(points)

    transformer: tfs.Transformer = tfs.Transformer.from_crs(
        crs_from,
        crs_to,
        always_xy=True,
    )

    transformed_points: list[shapely.Point] = [
        shapely.ops.transform(transformer.transform, point) for point in points
    ]
    tree: shapely.STRtree = shapely.STRtree(transformed_points)

    return CameraPoseIndex(camera_poses, transformer, tree)
