"""
Example script for finding spatially proximate camera poses between two camera groups.
"""

import click

from loguru import logger
from tqdm.auto import tqdm  # type: ignore[import-untyped]

from sealoc.dal import (
    DataAccessLayer,
    create_data_access_layer,
)
from sealoc.geometry import (
    CameraPoseIndex,
    CameraPoseLink,
    create_camera_pose_index,
)
from sealoc.models import (
    Camera,
    CameraBundle,
    CameraGroup,
    CameraPose,
)


def find_proximate_poses(
    database_url: str,
    bundle_label: str,
    max_distance: float,
) -> None:
    """
    Find cameras with proximate poses between the first two groups of a bundle.

    Arguments
    ---------
    database_url: Database URL string.
    bundle_label: Label of the camera bundle to load.
    max_distance: Maximum distance threshold in meters.
    """
    dal: DataAccessLayer = create_data_access_layer(database_url=database_url)

    with dal.session() as repos:
        bundle: CameraBundle | None = repos.bundles.get_one_by(label=bundle_label)
        if bundle is None:
            logger.error(f"Bundle '{bundle_label}' not found.")
            return

        groups: list[CameraGroup] = list(bundle.camera_groups)
        if len(groups) < 2:
            logger.error(f"Bundle '{bundle_label}' has fewer than two camera groups.")
            return

        group_a: CameraGroup = groups[0]
        group_b: CameraGroup = groups[1]
        logger.info(f"Comparing groups '{group_a.label}' and '{group_b.label}'.")

        poses_a: list[CameraPose] = collect_poses(group_a)
        poses_b: list[CameraPose] = collect_poses(group_b)

        logger.info(f"Group '{group_a.label}': {len(poses_a)} poses.")
        logger.info(f"Group '{group_b.label}': {len(poses_b)} poses.")

        if not poses_a or not poses_b:
            logger.warning("One or both groups have no poses.")
            return

        links: list[CameraPoseLink] = search_proximate_poses(
            poses_a, poses_b, max_distance
        )
        logger.info(
            f"Found {len(links)} pose pairs within {max_distance:.1f} m of each other."
        )

        for link in links[:5]:
            logger.info(
                f"  camera {link.query_pose.camera_id} <-> camera {link.database_pose.camera_id}"
                f"  distance={link.distance_meters:.2f} m"
            )


def collect_poses(group: CameraGroup) -> list[CameraPose]:
    """
    Collect poses from all cameras in a camera group.

    Arguments
    ---------
    group: Camera group to collect poses from.

    Returns
    -------
    Poses for cameras in the group that have one.
    """
    cameras: list[Camera] = list(group.cameras)
    return [
        camera.get_pose()  # type: ignore[misc]
        for camera in cameras
        if camera.has_pose()
    ]


def search_proximate_poses(
    database_poses: list[CameraPose],
    query_poses: list[CameraPose],
    max_distance: float,
) -> list[CameraPoseLink]:
    """
    Search for proximate poses between two sets of camera poses.

    Arguments
    ---------
    database_poses: Poses to index.
    query_poses: Poses to search with.
    max_distance: Maximum distance threshold in meters.

    Returns
    -------
    Links for all pose pairs within the distance threshold.
    """
    index: CameraPoseIndex = create_camera_pose_index(database_poses)

    links: list[CameraPoseLink] = []
    for pose in tqdm(query_poses, desc="Searching pose links"):
        links.extend(index.search_links(pose, max_distance))
    return links


@click.command()
@click.option("--database", "database_url", type=str, required=True)
@click.option("--bundle-label", type=str, required=True)
@click.option("--max-distance", type=float, default=1.0, show_default=True)
def main(database_url: str, bundle_label: str, max_distance: float) -> None:
    find_proximate_poses(database_url, bundle_label, max_distance)


if __name__ == "__main__":
    main()
