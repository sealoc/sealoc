"""
Data Access Layer providing a unified interface to camera model repositories
and image stores.
"""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import sealoc.database as db

from sealoc.environment import Environment, load_environment

from .repositories import (
    CameraBundleRepository,
    CameraGroupRepository,
)
from .stores import (
    ImageStore,
    create_image_store,
)


@dataclass(slots=True, frozen=True)
class Repositories:
    """
    All camera model repositories for a single database session.

    Attributes
    ----------
    bundles: Camera bundle repository.
    groups: Camera group repository.
    """

    bundles: CameraBundleRepository
    groups: CameraGroupRepository


@dataclass(slots=True, frozen=True)
class DataAccessLayer:
    """
    Unified access point for SEALOC data sources.

    Holds a database engine and an optional image store. Repositories are
    accessed within a session scope via `dal.session()`. Use `load_data_access_layer`
    to construct an instance.

    Attributes
    ----------
    engine: Database engine used for all sessions.
    image_store: Optional image store mapping labels to source paths.
    """

    engine: db.Engine
    image_store: ImageStore | None = None

    @contextmanager
    def session(self) -> Generator[Repositories, None, None]:
        """
        Open a database session and yield all camera model repositories.

        Commits on success and rolls back on exception, consistent with
        `db.session_scope`.

        Yields
        ------
        All camera model repositories bound to the open session.
        """
        with db.session_scope(self.engine) as session:
            yield Repositories(
                bundles=CameraBundleRepository(session=session),
                groups=CameraGroupRepository(session=session),
            )


def load_data_access_layer(
    database_url: str | None = None,
    image_dir: Path | str | None = None,
) -> DataAccessLayer:
    """
    Load a DataAccessLayer from the environment and optional overrides.

    Arguments
    ---------
    database_url: Database URL string. Overrides `SEALOC_DATABASE_URL` from the
        environment when provided. Raises `ValueError` if neither is available.
    image_dir: Path to the image directory. Overrides `SEALOC_IMAGE_DIRECTORY` from
        the environment when provided. `dal.image_store` will be `None` when neither
        is available.

    Returns
    -------
    Configured DataAccessLayer instance.
    """
    environment: Environment = load_environment()
    resolved_url: str | None = database_url or environment.database_url
    resolved_image_dir: Path | None = (
        Path(image_dir) if image_dir else environment.image_directory
    )

    if resolved_url is None:
        raise ValueError(
            "No database URL provided. Pass database_url explicitly or set SEALOC_DATABASE_URL."
        )

    db.validate_database_url(resolved_url)
    engine: db.Engine = db.create_engine(url=resolved_url)

    image_store: ImageStore | None = (
        create_image_store(image_dir=resolved_image_dir) if resolved_image_dir else None
    )
    return DataAccessLayer(engine=engine, image_store=image_store)
