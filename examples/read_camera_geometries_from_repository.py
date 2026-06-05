"""
Example script for reading camera poses and footprints via the data access layer.
"""

import click

import sealoc.models as models

from loguru import logger

from sealoc.dal import (
    DataAccessLayer,
    create_data_access_layer,
)
from sealoc.dal.repositories import (
    CameraFootprintRepository,
    CameraPoseRepository,
)


def read_camera_geometries(database_url: str) -> None:
    """
    Read camera geometries from a database.

    Arguments
    ---------
    database_url: Database URL string.
    """
    dal: DataAccessLayer = create_data_access_layer(database_url=database_url)

    with dal.session() as repos:
        read_camera_poses(repos.poses)
        read_camera_footprints(repos.footprints)


def read_camera_poses(
    repository: CameraPoseRepository,
) -> list[models.CameraPose]:
    """
    Read camera poses from a repository.

    Arguments
    ---------
    repository: Camera pose repository to read from.

    Returns
    -------
    List of all camera poses in the repository.
    """
    camera_pose_ids: list[int] = repository.get_all_ids()

    for camera_pose_id in camera_pose_ids[:10]:
        _camera_pose: models.CameraPose | None = repository.get_by_id(camera_pose_id)

    _invalid_camera_pose: models.CameraPose | None = repository.get_by_id(-1)

    logger.info("Reading camera poses...")
    camera_poses: list[models.CameraPose] = repository.get_all_by_ids(camera_pose_ids)
    logger.info(f"Read {len(camera_poses)} camera poses!")
    return camera_poses


def read_camera_footprints(
    repository: CameraFootprintRepository,
) -> list[models.CameraFootprint]:
    """
    Read camera footprints from a repository.

    Arguments
    ---------
    repository: Camera footprint repository to read from.

    Returns
    -------
    List of all camera footprints in the repository.
    """
    camera_footprint_ids: list[int] = repository.get_all_ids()

    for camera_footprint_id in camera_footprint_ids[:10]:
        _camera_footprint: models.CameraFootprint | None = repository.get_by_id(
            camera_footprint_id
        )

    _invalid_camera_footprint: models.CameraFootprint | None = repository.get_by_id(-1)

    logger.info("Reading camera footprints...")
    camera_footprints: list[models.CameraFootprint] = repository.get_all_by_ids(
        camera_footprint_ids
    )
    logger.info(f"Read {len(camera_footprints)} camera footprints!")
    return camera_footprints


@click.command()
@click.option("--database", "database_url", type=str, required=True)
def main(database_url: str) -> None:
    read_camera_geometries(database_url)


if __name__ == "__main__":
    main()
