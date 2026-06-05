"""
Domain models for camera calibration, sensor, pose, footprint, and grouping.
"""

from __future__ import annotations

import numpy as np
import shapely  # type: ignore[import-untyped]

import sealoc.transforms as tfs

from pydantic import (
    BaseModel,
    Field,
)


type Vec3 = tuple[float, float, float]
type Mat3 = tuple[Vec3, Vec3, Vec3]


def _default_sensor_location() -> Vec3:
    return (0.0, 0.0, 0.0)


def _default_sensor_rotation() -> Mat3:
    return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


class CameraCalibration(BaseModel):
    """
    Camera intrinsics and lens distortion parameters.
    """

    id: int
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    k1: float
    k2: float
    k3: float
    p1: float
    p2: float

    def __eq__(self, other: object) -> bool:
        """Checks if a camera calibration is equal to another."""
        if not isinstance(other, CameraCalibration):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Return a hash for the camera calibration."""
        return hash(self.id)

    @property
    def optical_center(self) -> tuple[float, float]:
        """
        Return the optical center of the calibration.

        Returns
        -------
        Optical center as (cx, cy).
        """
        return (self.cx, self.cy)

    @property
    def focal_length(self) -> float:
        """
        Return the focal length of the calibration.

        Returns
        -------
        Focal length fx.
        """
        return self.fx

    @property
    def intrinsic_matrix(self) -> np.ndarray:
        """
        Return the 3x3 camera intrinsic matrix.

        Returns
        -------
        3x3 intrinsic matrix K.
        """
        return np.array(
            [[self.fx, 0.0, self.cx], [0.0, self.fy, self.cy], [0.0, 0.0, 1.0]]
        )

    @property
    def distortion_vector(self) -> np.ndarray:
        """
        Return distortion coefficients as [k1, k2, p1, p2, k3].

        Returns
        -------
        Distortion coefficient vector [k1, k2, p1, p2, k3].
        """
        return np.array([self.k1, self.k2, self.p1, self.p2, self.k3])


class CameraSensor(BaseModel):
    """
    Physical sensor in a camera rig.
    """

    id: int
    label: str
    meta: dict = Field(default_factory=dict)
    width: int
    height: int

    location: Vec3 = Field(default_factory=_default_sensor_location)
    rotation: Mat3 = Field(default_factory=_default_sensor_rotation)

    calibration: CameraCalibration
    master_sensor: CameraSensor | None = Field(default=None)
    camera_group: CameraGroup | None = Field(default=None)

    def __hash__(self) -> int:
        """Returns a hash for the camera sensor."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Checks if a camera sensor is equal to another."""
        if not isinstance(other, CameraSensor):
            return NotImplemented
        return self.id == other.id

    @property
    def location_vector(self) -> np.ndarray:
        """
        Return the sensor location as a numpy array.

        Returns
        -------
        Location as a 1D array of shape (3,).
        """
        return np.array(self.location)

    @property
    def rotation_matrix(self) -> np.ndarray:
        """
        Return the sensor rotation as a numpy array.

        Returns
        -------
        Rotation as a 2D array of shape (3, 3).
        """
        return np.array(self.rotation)

    @property
    def transform(self) -> tfs.RigidTransform:
        """
        Return the sensor pose as a rigid body transformation relative to the rig origin.

        For a slave sensor this is the extrinsic transform relative to the master.
        For a master sensor this is the identity transform.

        Returns
        -------
        Rigid body transformation with rotation and translation.
        """
        return tfs.RigidTransform.from_components(
            translation=self.location_vector,
            rotation=tfs.Rotation.from_matrix(self.rotation_matrix),
        )

    @property
    def is_master(self) -> bool:
        """
        Return True if the sensor does not have a master sensor.

        Returns
        -------
        True if this is a master sensor.
        """
        return self.master_sensor is None

    @property
    def is_slave(self) -> bool:
        """
        Return True if the sensor has a master sensor.

        Returns
        -------
        True if this is a slave sensor.
        """
        return not self.is_master


class CameraPose(BaseModel):
    """
    Georeferenced camera pose with orientation angles.
    """

    camera_id: int
    location: Vec3
    srid: int

    yaw: float
    pitch: float
    roll: float

    def __hash__(self) -> int:
        """Return a hash based on the camera id."""
        return self.camera_id

    @property
    def shape(self) -> shapely.Point:
        """
        Return the camera pose as a shapely Point.

        Returns
        -------
        Point at the camera location.
        """
        return shapely.Point(self.location)

    @property
    def crs(self) -> tfs.CRS:
        """
        Return the CRS of the camera pose.

        Returns
        -------
        CRS corresponding to the pose SRID.
        """
        return tfs.CRS.from_epsg(self.srid)

    @property
    def epsg_code(self) -> int:
        """
        Return the EPSG code for the pose.

        Returns
        -------
        EPSG integer code.
        """
        return self.srid

    @property
    def epsg_string(self) -> str:
        """
        Return the EPSG code as a string.

        Returns
        -------
        EPSG code in "EPSG:<srid>" format.
        """
        return f"EPSG:{self.srid}"


class CameraFootprint(BaseModel):
    """
    Georeferenced camera footprint.
    """

    camera_id: int
    coordinates: list[Vec3]
    srid: int

    def __hash__(self) -> int:
        """Return a hash based on the camera id."""
        return self.camera_id

    @property
    def shape(self) -> shapely.Polygon:
        """
        Return the footprint shape as a polygon.

        Returns
        -------
        Polygon built from the footprint coordinates.
        """
        return shapely.Polygon(self.coordinates)

    @property
    def crs(self) -> tfs.CRS:
        """
        Return the CRS of the camera footprint.

        Returns
        -------
        CRS corresponding to the footprint SRID.
        """
        return tfs.CRS.from_epsg(self.srid)

    @property
    def centroid(self) -> shapely.Point:
        """
        Return the centroid of the footprint polygon.

        Returns
        -------
        Centroid point of the footprint.
        """
        return shapely.centroid(self.shape)

    @property
    def epsg_code(self) -> int:
        """
        Return the EPSG code for the footprint.

        Returns
        -------
        EPSG integer code.
        """
        return self.srid

    @property
    def epsg_string(self) -> str:
        """
        Return the EPSG code as a string.

        Returns
        -------
        EPSG code in "EPSG:<srid>" format.
        """
        return f"EPSG:{self.srid}"


class Camera(BaseModel):
    """
    Image view linked to a sensor and optional spatial data.
    """

    id: int
    label: str
    image_label: str
    meta: dict = Field(default_factory=dict)

    camera_sensor: CameraSensor
    master_camera: Camera | None = Field(default=None)
    camera_group: CameraGroup | None = Field(default=None)

    camera_pose: CameraPose | None = Field(default=None)
    camera_footprint: CameraFootprint | None = Field(default=None)

    def __hash__(self) -> int:
        """Returns the hash for the camera schema."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Checks if a camera is equal to another."""
        if not isinstance(other, Camera):
            return NotImplemented
        return self.id == other.id

    @property
    def sensor(self) -> CameraSensor:
        """
        Return the camera sensor.

        Returns
        -------
        Sensor attached to this camera.
        """
        return self.camera_sensor

    @property
    def is_master(self) -> bool:
        """
        Return True if the camera does not have a master camera.

        Returns
        -------
        True if this is a master camera.
        """
        return self.master_camera is None

    @property
    def is_slave(self) -> bool:
        """
        Return True if the camera has a master camera.

        Returns
        -------
        True if this is a slave camera.
        """
        return not self.is_master

    def set_pose(self, camera_pose: CameraPose) -> None:
        """
        Set the camera pose.

        Arguments
        ---------
        camera_pose: Pose to attach to this camera.
        """
        self.camera_pose = camera_pose

    def get_pose(self) -> CameraPose | None:
        """
        Return the camera pose.

        Returns
        -------
        Attached camera pose, or None if not set.
        """
        return self.camera_pose

    def has_pose(self) -> bool:
        """
        Return True if a camera pose is attached.

        Returns
        -------
        True if a pose is attached to this camera.
        """
        return self.camera_pose is not None

    def set_footprint(self, camera_footprint: CameraFootprint) -> None:
        """
        Set the camera footprint.

        Arguments
        ---------
        camera_footprint: Footprint to attach to this camera.
        """
        self.camera_footprint = camera_footprint

    def get_footprint(self) -> CameraFootprint | None:
        """
        Return the camera footprint.

        Returns
        -------
        Attached camera footprint, or None if not set.
        """
        return self.camera_footprint

    def has_footprint(self) -> bool:
        """
        Return True if a camera footprint is attached.

        Returns
        -------
        True if a footprint is attached to this camera.
        """
        return self.camera_footprint is not None


class CameraGroup(BaseModel):
    """
    Collection of related cameras and sensors.
    """

    id: int
    label: str
    meta: dict = Field(default_factory=dict)

    camera_sensors: set[CameraSensor] = Field(default_factory=set)
    cameras: set[Camera] = Field(default_factory=set)
    camera_bundle: CameraBundle | None = Field(default=None)

    def __eq__(self, other: object) -> bool:
        """Checks if a camera group is equal to another."""
        if not isinstance(other, CameraGroup):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Return a hash for the camera group."""
        return hash(self.id)

    @property
    def camera_poses(self) -> list[CameraPose]:
        """
        Return the poses of all cameras in the group that have a pose.

        Returns
        -------
        Poses for all cameras in this group that have a pose attached.
        """
        return [
            camera.camera_pose
            for camera in self.cameras
            if camera.camera_pose is not None
        ]

    @property
    def camera_footprints(self) -> list[CameraFootprint]:
        """
        Return the footprints of all cameras in the group that have a footprint.

        Returns
        -------
        Footprints for all cameras in this group that have a footprint attached.
        """
        return [
            camera.camera_footprint
            for camera in self.cameras
            if camera.camera_footprint is not None
        ]

    def add_sensor(self, camera_sensor: CameraSensor) -> None:
        """
        Add a camera sensor to the camera group.

        Arguments
        ---------
        camera_sensor: Sensor to add.
        """
        camera_sensor.camera_group = self
        self.camera_sensors.add(camera_sensor)

    def add_camera(self, camera: Camera) -> None:
        """
        Add a camera to the camera group.

        Arguments
        ---------
        camera: Camera to add.
        """
        camera.camera_group = self
        self.cameras.add(camera)


class CameraBundle(BaseModel):
    """
    Top-level container for camera groups.
    """

    id: int
    label: str
    meta: dict = Field(default_factory=dict)

    camera_groups: set[CameraGroup] = Field(default_factory=set)

    @property
    def camera_sensors(self) -> list[CameraSensor]:
        """
        Return the camera sensors in the bundle.

        Returns
        -------
        All sensors across all camera groups in this bundle.
        """
        return [
            sensor for group in self.camera_groups for sensor in group.camera_sensors
        ]

    @property
    def cameras(self) -> list[Camera]:
        """
        Return the cameras in the bundle.

        Returns
        -------
        All cameras across all camera groups in this bundle.
        """
        return [camera for group in self.camera_groups for camera in group.cameras]

    @property
    def groups(self) -> set[CameraGroup]:
        """
        Return the camera groups in the bundle.

        Returns
        -------
        Set of camera groups in this bundle.
        """
        return self.camera_groups

    def add_group(self, camera_group: CameraGroup) -> None:
        """
        Add a camera group to the camera bundle.

        Arguments
        ---------
        camera_group: Camera group to add.
        """
        camera_group.camera_bundle = self
        self.camera_groups.add(camera_group)
