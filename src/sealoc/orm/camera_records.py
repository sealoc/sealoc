"""
ORM models for camera bundles, sensors, views, poses, and footprints.
"""

import textwrap

import sqlmodel as sqlm

from typing import (
    Any,
    Optional,
)


type Vec3 = tuple[float, float, float]
type Mat3 = tuple[Vec3, Vec3, Vec3]


class CameraBundleRecord(sqlm.SQLModel, table=True):
    """
    Top-level container for related camera groups in a single project.

    A bundle does not store cameras or sensors directly; it aggregates
    CameraGroupRecord instances that hold the concrete sensors and views.
    """

    id: Optional[int] = sqlm.Field(default=None, primary_key=True)
    label: str = ""
    meta: dict = sqlm.Field(default_factory=dict, sa_type=sqlm.JSON)

    camera_groups: list["CameraGroupRecord"] = sqlm.Relationship(
        back_populates="bundle",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __str__(self) -> str:
        """Returns a string representation of the object."""
        attributes: str = (
            f"id={self.id}, "
            f"label={self.label}, "
            f"camera_groups={len(self.camera_groups)}"
        )
        return f"{self.__class__.__name__}({textwrap.shorten(attributes, width=80)})"

    @property
    def cameras(self) -> list["CameraRecord"]:
        """
        Return the cameras in the camera groups.

        Returns
        -------
        All cameras across all camera groups in this bundle.
        """
        bundle_cameras: list = list()
        for group in self.camera_groups:
            bundle_cameras.extend(group.cameras)
        return bundle_cameras

    @property
    def sensors(self) -> list["CameraSensorRecord"]:
        """
        Return the sensors in the camera groups.

        Returns
        -------
        All sensors across all camera groups in this bundle.
        """
        bundle_sensors: list = list()
        for group in self.camera_groups:
            bundle_sensors.extend(group.sensors)
        return bundle_sensors


class CameraGroupRecord(sqlm.SQLModel, table=True):
    """
    Group of cameras and sensors that share a common context.

    Each group belongs to a single CameraBundleRecord and typically represents
    one rig, flight line, or acquisition session.
    """

    id: Optional[int] = sqlm.Field(default=None, primary_key=True)
    label: str = ""
    meta: dict = sqlm.Field(default_factory=dict, sa_type=sqlm.JSON)

    bundle_id: Optional[int] = sqlm.Field(
        default=None,
        foreign_key="camerabundlerecord.id",
        index=True,
    )
    bundle: Optional["CameraBundleRecord"] = sqlm.Relationship(
        back_populates="camera_groups",
    )

    sensors: list["CameraSensorRecord"] = sqlm.Relationship(
        back_populates="camera_group",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    cameras: list["CameraRecord"] = sqlm.Relationship(
        back_populates="camera_group",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class CalibrationBaseRecord(sqlm.SQLModel):
    """
    Intrinsic camera parameters following OpenCV pinhole + distortion conventions.

    Stores image size, focal lengths, principal point, and radial/tangential
    distortion coefficients compatible with cv::calibrateCamera.
    """

    width: int
    height: int
    fx: float
    fy: float
    cx: float  # optical center as per OpenCV
    cy: float  # optical center as per OpenCV
    k1: float  # radial distortion as per OpenCV
    k2: float  # radial distortion as per OpenCV
    k3: float  # radial distortion as per OpenCV
    p1: float  # tangential distortion as per OpenCV
    p2: float  # tangential distortion as per OpenCV


class CameraCalibrationRecord(CalibrationBaseRecord, table=True):
    """
    Stored intrinsic calibration for a single camera sensor.
    """

    id: Optional[int] = sqlm.Field(default=None, primary_key=True)

    # Create a one-to-one mapping between a sensor and a calibration
    sensor: "CameraSensorRecord" = sqlm.Relationship(
        back_populates="calibration",
        sa_relationship_kwargs={"uselist": False, "lazy": "selectin"},
    )


class CameraSensorBaseRecord(sqlm.SQLModel):
    """
    Base fields for a camera sensor.

    Represents a physical imaging device with image size and optional
    3D pose (location and rotation).
    """

    label: str = sqlm.Field(default="")
    width: int
    height: int

    # store location as JSON array
    location: Optional[Vec3] = sqlm.Field(
        default=None,
        sa_type=sqlm.JSON,
    )

    # store rotation as JSON nested array
    rotation: Optional[Mat3] = sqlm.Field(
        default=None,
        sa_type=sqlm.JSON,
    )


class CameraSensorRecord(CameraSensorBaseRecord, table=True):
    """
    Physical camera sensor with intrinsic calibration.

    A sensor can be master or slave in a stereo rig and is linked to one or more
    CameraRecord views captured by this sensor.
    """

    id: Optional[int] = sqlm.Field(default=None, primary_key=True)

    camera_group_id: Optional[int] = sqlm.Field(
        default=None, foreign_key="cameragrouprecord.id", index=True
    )
    camera_group: Optional["CameraGroupRecord"] = sqlm.Relationship(
        back_populates="sensors"
    )

    calibration_id: Optional[int] = sqlm.Field(
        default=None, foreign_key="cameracalibrationrecord.id"
    )
    calibration: Optional["CameraCalibrationRecord"] = sqlm.Relationship(
        back_populates="sensor",
        sa_relationship_kwargs={"uselist": False},
    )

    # Master sensor id (one-to-many: master -> slaves)
    master_sensor_id: Optional[int] = sqlm.Field(
        default=None,
        foreign_key="camerasensorrecord.id",
        nullable=True,
    )

    # Many-to-one: slave -> master
    master_sensor: Optional["CameraSensorRecord"] = sqlm.Relationship(
        back_populates="slave_sensors",
        sa_relationship_kwargs={
            "remote_side": "CameraSensorRecord.id",
            "foreign_keys": "CameraSensorRecord.master_sensor_id",
        },
    )

    # One-to-many: master -> slaves
    slave_sensors: list["CameraSensorRecord"] = sqlm.Relationship(
        back_populates="master_sensor",
        sa_relationship_kwargs={
            "foreign_keys": "CameraSensorRecord.master_sensor_id",
        },
    )

    # Cameras captured by the sensor
    cameras: list["CameraRecord"] = sqlm.Relationship(back_populates="sensor")

    def __str__(self) -> str:
        """
        Return a short summary including id, label, and calibration.
        """
        if self.calibration:
            calibration_string = f"{self.calibration.id}"
        else:
            calibration_string = f"{self.calibration}"

        attributes: str = f"""
            id={self.id},
            label={self.label},
            calibration={calibration_string}
        """
        return f"{self.__class__.__name__}({textwrap.shorten(attributes, width=80)})"


class CameraBaseRecord(sqlm.SQLModel):
    """
    Common metadata fields for a camera view.
    """

    label: str
    image_label: str
    meta: dict[str, Any] = sqlm.Field(
        default_factory=dict,
        sa_type=sqlm.JSON,
    )


class CameraRecord(CameraBaseRecord, table=True):
    """
    Single camera view (image or frame) in the dataset.

    Each view is captured by one CameraSensorRecord and may be part of a
    master–slave camera pair.
    """

    id: Optional[int] = sqlm.Field(default=None, primary_key=True)

    camera_group_id: Optional[int] = sqlm.Field(
        default=None, foreign_key="cameragrouprecord.id", index=True
    )
    camera_group: Optional["CameraGroupRecord"] = sqlm.Relationship(
        back_populates="cameras"
    )

    # One-to-many: (sensor -> cameras)
    sensor_id: Optional[int] = sqlm.Field(
        default=None, foreign_key="camerasensorrecord.id"
    )

    sensor: "CameraSensorRecord" = sqlm.Relationship(back_populates="cameras")

    # Master camera id (one-to-many: master -> slaves)
    master_camera_id: Optional[int] = sqlm.Field(
        default=None,
        foreign_key="camerarecord.id",
        nullable=True,
    )

    # Many-to-one: slave -> master
    master_camera: Optional["CameraRecord"] = sqlm.Relationship(
        back_populates="slave_cameras",
        sa_relationship_kwargs={
            "remote_side": "CameraRecord.id",
            "foreign_keys": "CameraRecord.master_camera_id",
        },
    )

    # One-to-many: master -> slaves
    slave_cameras: list["CameraRecord"] = sqlm.Relationship(
        back_populates="master_camera",
        sa_relationship_kwargs={
            "foreign_keys": "CameraRecord.master_camera_id",
        },
    )

    camera_pose: Optional["CameraPoseRecord"] = sqlm.Relationship(
        back_populates="camera",
        sa_relationship_kwargs={"uselist": False, "lazy": "selectin"},
    )

    camera_footprint: Optional["CameraFootprintRecord"] = sqlm.Relationship(
        back_populates="camera",
        sa_relationship_kwargs={"uselist": False, "lazy": "selectin"},
    )


class CameraPoseRecord(sqlm.SQLModel, table=True):
    """
    Georeferenced pose of a camera in a given CRS.

    Stores camera position (location) in the EPSG CRS given by srid and
    orientation as yaw, pitch, and roll angles.
    Angles are in degrees using a yaw–pitch–roll (Z–Y–X) convention.
    """

    camera_id: int = sqlm.Field(foreign_key="camerarecord.id", primary_key=True)
    location: Vec3 = sqlm.Field(sa_type=sqlm.JSON)
    srid: int = sqlm.Field(default=4326)

    yaw: float
    pitch: float
    roll: float

    camera: Optional["CameraRecord"] = sqlm.Relationship(
        back_populates="camera_pose",
    )


class CameraFootprintRecord(sqlm.SQLModel, table=True):
    """
    Ground footprint of a camera view in a given CRS.

    Stores the projected polygon of the image in the EPSG CRS given by srid.
    """

    camera_id: int = sqlm.Field(foreign_key="camerarecord.id", primary_key=True)
    polygon: list[Vec3] = sqlm.Field(sa_type=sqlm.JSON)
    srid: int = sqlm.Field(default=4326)

    camera: Optional["CameraRecord"] = sqlm.Relationship(
        back_populates="camera_footprint",
    )
