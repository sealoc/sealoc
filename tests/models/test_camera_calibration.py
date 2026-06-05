"""Unit tests for sealoc.models.CameraCalibration."""

from __future__ import annotations

import numpy as np
import pytest

from sealoc.models import CameraCalibration


_CALIBRATION = CameraCalibration(
    id=1,
    width=1920,
    height=1080,
    fx=800.0,
    fy=802.0,
    cx=960.0,
    cy=540.0,
    k1=0.1,
    k2=0.2,
    k3=0.3,
    p1=0.01,
    p2=0.02,
)


def test_optical_center() -> None:
    """optical_center returns (cx, cy)."""
    assert _CALIBRATION.optical_center == (960.0, 540.0)


def test_focal_length() -> None:
    """focal_length returns fx."""
    assert _CALIBRATION.focal_length == 800.0


def test_intrinsic_matrix_shape() -> None:
    """intrinsic_matrix is a 3x3 array."""
    assert _CALIBRATION.intrinsic_matrix.shape == (3, 3)


def test_intrinsic_matrix_values() -> None:
    """intrinsic_matrix encodes fx, fy, cx, cy correctly."""
    K = _CALIBRATION.intrinsic_matrix
    assert K[0, 0] == pytest.approx(800.0)
    assert K[1, 1] == pytest.approx(802.0)
    assert K[0, 2] == pytest.approx(960.0)
    assert K[1, 2] == pytest.approx(540.0)
    assert K[2, 2] == pytest.approx(1.0)
    assert K[0, 1] == pytest.approx(0.0)
    assert K[1, 0] == pytest.approx(0.0)


def test_distortion_vector_order() -> None:
    """distortion_vector is [k1, k2, p1, p2, k3]."""
    distortion = _CALIBRATION.distortion_vector
    assert distortion.shape == (5,)
    expected = np.array([0.1, 0.2, 0.01, 0.02, 0.3])
    np.testing.assert_array_almost_equal(distortion, expected)
