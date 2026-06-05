"""
Module for camera links including link types and factories.
"""

from pydantic import BaseModel

from sealoc.models import (
    CameraFootprint,
    CameraPose,
)


class CameraPoseLink(BaseModel):
    """
    Geometric link between a query and database camera via pose proximity.

    Attributes
    ----------
    database_pose: Pose of the matched database camera.
    query_pose: Pose of the query camera.
    distance_meters: Distance between the two poses in meters.
    """

    database_pose: CameraPose
    query_pose: CameraPose

    distance_meters: float

    @property
    def query_camera_id(self) -> int:
        """
        Return the query camera id from the link.

        Returns
        -------
        Camera id of the query camera.
        """
        return self.query_pose.camera_id

    @property
    def database_camera_id(self) -> int:
        """
        Return the database camera id from the link.

        Returns
        -------
        Camera id of the database camera.
        """
        return self.database_pose.camera_id


class CameraFootprintLink(BaseModel):
    """
    Geometric link between a query and database camera via footprint overlap.

    Attributes
    ----------
    database_footprint: Footprint of the matched database camera.
    query_footprint: Footprint of the query camera.
    database_footprint_area: Area of the database footprint.
    query_footprint_area: Area of the query footprint.
    footprint_iou: Intersection-over-union of the two footprints.
    """

    database_footprint: CameraFootprint
    query_footprint: CameraFootprint

    database_footprint_area: float
    query_footprint_area: float
    footprint_iou: float

    @property
    def query_camera_id(self) -> int:
        """
        Return the query camera id from the link.

        Returns
        -------
        Camera id of the query camera.
        """
        return self.query_footprint.camera_id

    @property
    def database_camera_id(self) -> int:
        """
        Return the database camera id from the link.

        Returns
        -------
        Camera id of the database camera.
        """
        return self.database_footprint.camera_id
