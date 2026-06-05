"""
Example script for finding cameras with overlapping footprints between two camera groups.
"""

import click

from loguru import logger
from tqdm.auto import tqdm  # type: ignore[import-untyped]

from sealoc.dal import (
    DataAccessLayer,
    create_data_access_layer,
)
from sealoc.geometry import (
    CameraFootprintIndex,
    CameraFootprintLink,
    create_camera_footprint_index,
)
from sealoc.models import (
    Camera,
    CameraBundle,
    CameraFootprint,
    CameraGroup,
)


def find_overlapping_footprints(
    database_url: str,
    bundle_label: str,
) -> None:
    """
    Find cameras with overlapping footprints between the first two groups of a bundle.

    Arguments
    ---------
    database_url: Database URL string.
    bundle_label: Label of the camera bundle to load.
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

        footprints_a: list[CameraFootprint] = collect_footprints(group_a)
        footprints_b: list[CameraFootprint] = collect_footprints(group_b)

        logger.info(f"Group '{group_a.label}': {len(footprints_a)} footprints.")
        logger.info(f"Group '{group_b.label}': {len(footprints_b)} footprints.")

        if not footprints_a or not footprints_b:
            logger.warning("One or both groups have no footprints.")
            return

        links: list[CameraFootprintLink] = search_overlapping_footprints(
            footprints_a, footprints_b
        )
        logger.info(f"Found {len(links)} overlapping footprint pairs.")

        for link in links[:5]:
            logger.info(
                f"  camera {link.query_camera_id} <-> camera {link.database_camera_id}"
                f"  IoU={link.footprint_iou:.3f}"
            )


def collect_footprints(group: CameraGroup) -> list[CameraFootprint]:
    """
    Collect footprints from all cameras in a camera group.

    Arguments
    ---------
    group: Camera group to collect footprints from.

    Returns
    -------
    Footprints for cameras in the group that have one.
    """
    cameras: list[Camera] = list(group.cameras)
    return [
        camera.get_footprint()  # type: ignore[misc]
        for camera in cameras
        if camera.has_footprint()
    ]


def search_overlapping_footprints(
    database_footprints: list[CameraFootprint],
    query_footprints: list[CameraFootprint],
) -> list[CameraFootprintLink]:
    """
    Search for overlapping footprints between two sets of camera footprints.

    Arguments
    ---------
    database_footprints: Footprints to index.
    query_footprints: Footprints to search with.

    Returns
    -------
    Links for all overlapping footprint pairs.
    """
    index: CameraFootprintIndex = create_camera_footprint_index(database_footprints)

    links: list[CameraFootprintLink] = []
    for footprint in tqdm(query_footprints, desc="Searching footprint links"):
        links.extend(index.search_links(footprint))
    return links


@click.command()
@click.option("--database", "database_url", type=str, required=True)
@click.option("--bundle-label", type=str, required=True)
def main(database_url: str, bundle_label: str) -> None:
    find_overlapping_footprints(database_url, bundle_label)


if __name__ == "__main__":
    main()
