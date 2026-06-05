"""
Package for processing camera poses and footprints.
The package includes indices for finding overlapping camera footprints and spatially
proximate camera poses, along with link types and metric functions.
"""

from .footprint_index import (
    CameraFootprintIndex as CameraFootprintIndex,
    create_camera_footprint_index as create_camera_footprint_index,
)

from .footprint_metrics import (
    calculate_footprint_area as calculate_footprint_area,
    calculate_footprint_iou as calculate_footprint_iou,
    calculate_footprint_intersection_area as calculate_footprint_intersection_area,
    calculate_footprint_union_area as calculate_footprint_union_area,
)

from .pose_index import (
    CameraPoseIndex as CameraPoseIndex,
    create_camera_pose_index as create_camera_pose_index,
)

from .pose_metrics import (
    calculate_point_distance as calculate_point_distance,
    calculate_pose_distance as calculate_pose_distance,
)

from .types import (
    CameraFootprintLink as CameraFootprintLink,
    CameraPoseLink as CameraPoseLink,
)

__all__ = []
