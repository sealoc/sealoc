"""
Example script for reading camera bundles and groups via the data access layer.
"""

import click

from loguru import logger

from sealoc.dal import (
    DataAccessLayer,
    create_data_access_layer,
)
from sealoc.dal.repositories import (
    CameraBundleRepository,
    CameraGroupRepository,
)
from sealoc.models import (
    CameraBundle,
    CameraGroup,
)


def read_models_from_repository(database_url: str) -> None:
    """
    Read camera models from repositories.

    Arguments
    ---------
    database_url: Database URL string.
    """
    dal: DataAccessLayer = create_data_access_layer(database_url=database_url)

    with dal.session() as repos:
        read_camera_groups_from_repository(repos.groups)
        read_camera_bundles_from_repository(repos.bundles)


def read_camera_groups_from_repository(repository: CameraGroupRepository) -> None:
    """
    Read camera groups from a repository.

    Arguments
    ---------
    repository: Camera group repository to read from.
    """
    all_group_ids: set[int] = repository.get_all_ids()
    logger.info(f"Camera group ids: {all_group_ids}")

    for group_id in all_group_ids:
        camera_group: CameraGroup | None = repository.get_by_id(group_id)
        if camera_group is not None:
            logger.info(f"Read by id: {camera_group.label}")

    for group_id in all_group_ids:
        camera_group = repository.get_one_by(id=group_id)
        if camera_group is not None:
            logger.info(f"Read one by attribute: {camera_group.label}")

    for group_id in all_group_ids:
        camera_groups: list[CameraGroup] = repository.get_all_by(id=group_id)
        logger.info(
            f"Read all by attribute: {[group.label for group in camera_groups]}"
        )


def read_camera_bundles_from_repository(repository: CameraBundleRepository) -> None:
    """
    Read camera bundles from a repository.

    Arguments
    ---------
    repository: Camera bundle repository to read from.
    """
    all_bundle_ids: set[int] = repository.get_all_ids()
    logger.info(f"Camera bundle ids: {all_bundle_ids}")

    for bundle_id in all_bundle_ids:
        camera_bundle: CameraBundle | None = repository.get_by_id(bundle_id)
        if camera_bundle is not None:
            logger.info(f"Read by id: {camera_bundle.label}")

    for bundle_id in all_bundle_ids:
        camera_bundle = repository.get_one_by(id=bundle_id)
        if camera_bundle is not None:
            logger.info(f"Read one by attribute: {camera_bundle.label}")

    for bundle_id in all_bundle_ids:
        camera_bundles: list[CameraBundle] = repository.get_all_by(id=bundle_id)
        logger.info(
            f"Read all by attribute: {[bundle.label for bundle in camera_bundles]}"
        )


@click.command()
@click.option("--database", "database_url", type=str, required=True)
def main(database_url: str) -> None:
    read_models_from_repository(database_url)


if __name__ == "__main__":
    main()
