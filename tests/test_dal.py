"""
Unit tests for the sealoc Data Access Layer.
"""

from __future__ import annotations

import pytest

from pathlib import Path

import sealoc.database as db
import sealoc.orm as orm

from pydantic import ValidationError

from sealoc.dal import (
    DataAccessLayer,
    Repositories,
    create_data_access_layer,
)
from sealoc.dal.repositories import (
    CameraBundleRepository,
    CameraGroupRepository,
)
from sealoc.dal.stores import ImageStore


def _make_db(tmp_path: Path) -> str:
    """Create an empty sealoc SQLite database and return its URL."""
    db_path = tmp_path / "test.db"
    db_path.touch()
    url = f"sqlite:///{db_path}"
    engine = db.create_engine(url=url)
    orm.create_orm_tables(engine)
    return url


def test_create_data_access_layer_with_explicit_url(tmp_path: Path) -> None:
    """create_data_access_layer returns a DAL with a live engine when given an explicit database URL."""
    url = _make_db(tmp_path)
    dal = create_data_access_layer(database_url=url)

    assert isinstance(dal, DataAccessLayer)
    assert isinstance(dal.engine, db.Engine)


def test_create_data_access_layer_with_env_fallback(
    monkeypatch, tmp_path: Path
) -> None:
    """create_data_access_layer resolves the database URL from SEALOC_DATABASE_URL when no argument is given."""
    url = _make_db(tmp_path)
    monkeypatch.setenv("SEALOC_DATABASE_URL", url)

    dal = create_data_access_layer()

    assert isinstance(dal, DataAccessLayer)
    assert isinstance(dal.engine, db.Engine)


def test_create_data_access_layer_raises_without_database(
    monkeypatch, tmp_path: Path
) -> None:
    """create_data_access_layer raises ValidationError when no URL is provided and env var is unset."""
    monkeypatch.delenv("SEALOC_DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError):
        create_data_access_layer()


def test_create_data_access_layer_without_image_store(tmp_path: Path) -> None:
    """dal.image_store is None when image_dir is not provided."""
    url = _make_db(tmp_path)
    dal = create_data_access_layer(database_url=url)

    assert dal.image_store is None


def test_create_data_access_layer_with_image_store(tmp_path: Path) -> None:
    """dal.image_store is an ImageStore when a valid image_dir is provided."""
    url = _make_db(tmp_path)
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    dal = create_data_access_layer(database_url=url, image_dir=image_dir)

    assert isinstance(dal.image_store, ImageStore)


def test_create_data_access_layer_image_store_env_fallback(
    monkeypatch, tmp_path: Path
) -> None:
    """dal.image_store is populated from SEALOC_IMAGE_DIRECTORY when neither image_dir nor database_url args are given."""
    url = _make_db(tmp_path)
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    monkeypatch.setenv("SEALOC_DATABASE_URL", url)
    monkeypatch.setenv("SEALOC_IMAGE_DIRECTORY", str(image_dir))

    dal = create_data_access_layer()

    assert isinstance(dal.image_store, ImageStore)


def test_create_data_access_layer_image_store_absent_without_env_or_arg(
    tmp_path: Path,
) -> None:
    """dal.image_store is None when neither image_dir arg nor SEALOC_IMAGE_DIR env var is set."""
    url = _make_db(tmp_path)
    dal = create_data_access_layer(database_url=url)

    assert dal.image_store is None


def test_session_yields_repositories(tmp_path: Path) -> None:
    """dal.session() yields a Repositories instance with bundle and group repositories."""
    url = _make_db(tmp_path)
    dal = create_data_access_layer(database_url=url)

    with dal.session() as repos:
        assert isinstance(repos, Repositories)
        assert isinstance(repos.bundles, CameraBundleRepository)
        assert isinstance(repos.groups, CameraGroupRepository)
