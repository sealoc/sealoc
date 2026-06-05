"""Unit tests for sealoc.models.CameraSensor."""

from __future__ import annotations

import numpy as np

from scipy.spatial.transform import RigidTransform  # type: ignore[import-untyped]

from sealoc.models import CameraCalibration, CameraSensor


_CALIBRATION = CameraCalibration(
    id=1,
    width=1920,
    height=1080,
    fx=800.0,
    fy=800.0,
    cx=960.0,
    cy=540.0,
    k1=0.0,
    k2=0.0,
    k3=0.0,
    p1=0.0,
    p2=0.0,
)

_MASTER_SENSOR = CameraSensor(
    id=1,
    label="left",
    width=1920,
    height=1080,
    calibration=_CALIBRATION,
)

_SLAVE_SENSOR = CameraSensor(
    id=2,
    label="right",
    width=1920,
    height=1080,
    location=(0.12, 0.0, 0.0),
    rotation=(
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    ),
    calibration=_CALIBRATION,
    master_sensor=_MASTER_SENSOR,
)


def test_master_sensor_is_master() -> None:
    """A sensor without a master_sensor is a master."""
    assert _MASTER_SENSOR.is_master is True
    assert _MASTER_SENSOR.is_slave is False


def test_slave_sensor_is_slave() -> None:
    """A sensor with a master_sensor is a slave."""
    assert _SLAVE_SENSOR.is_slave is True
    assert _SLAVE_SENSOR.is_master is False


def test_location_vector_shape() -> None:
    """location_vector is a 1D array of shape (3,)."""
    assert _SLAVE_SENSOR.location_vector.shape == (3,)


def test_location_vector_values() -> None:
    """location_vector matches the location tuple."""
    np.testing.assert_array_almost_equal(
        _SLAVE_SENSOR.location_vector, np.array([0.12, 0.0, 0.0])
    )


def test_rotation_matrix_shape() -> None:
    """rotation_matrix is a 2D array of shape (3, 3)."""
    assert _SLAVE_SENSOR.rotation_matrix.shape == (3, 3)


def test_rotation_matrix_default_is_identity() -> None:
    """Default rotation matrix is the 3x3 identity."""
    np.testing.assert_array_almost_equal(_MASTER_SENSOR.rotation_matrix, np.eye(3))


def test_transform_returns_rigid_transform() -> None:
    """transform returns a RigidTransform instance."""
    assert isinstance(_SLAVE_SENSOR.transform, RigidTransform)


def test_transform_translation() -> None:
    """transform translation matches the sensor location vector."""
    np.testing.assert_array_almost_equal(
        _SLAVE_SENSOR.transform.translation, np.array([0.12, 0.0, 0.0])
    )


def test_transform_rotation() -> None:
    """transform rotation matrix matches the sensor rotation matrix."""
    np.testing.assert_array_almost_equal(
        _SLAVE_SENSOR.transform.rotation.as_matrix(), np.eye(3)
    )


def test_master_transform_is_identity() -> None:
    """Master sensor transform has zero translation and identity rotation."""
    transform = _MASTER_SENSOR.transform
    np.testing.assert_array_almost_equal(transform.translation, np.zeros(3))
    np.testing.assert_array_almost_equal(transform.rotation.as_matrix(), np.eye(3))
