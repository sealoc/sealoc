"""Module for transform constants."""

import numpy as np

LONGITUDE_UPPER_DEG: float = 180.0
LONGITUDE_LOWER_DEG: float = -180.0

LONGITUDE_UPPER_RAD: float = np.deg2rad(LONGITUDE_UPPER_DEG)
LONGITUDE_LOWER_RAD: float = np.deg2rad(LONGITUDE_LOWER_DEG)

LATITUDE_UPPER_DEG: float = 90.0
LATITUDE_LOWER_DEG: float = -90.0

LATITUDE_UPPER_RAD: float = np.deg2rad(LATITUDE_UPPER_DEG)
LATITUDE_LOWER_RAD: float = np.deg2rad(LATITUDE_LOWER_DEG)
