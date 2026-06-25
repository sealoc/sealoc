"""Unit tests for the sealoc environment module."""

from __future__ import annotations

from pathlib import Path

from sealoc.environment import Environment, load_environment


def test_load_environment_returns_valid_environment(tmp_path: Path) -> None:
    """load_environment() returns a valid Environment when SEALOC_DATABASE_URL is set."""
    env_file: Path = tmp_path / ".env"
    env_file.write_text('SEALOC_DATABASE_URL="sqlite:////data/sealoc.db"\n')

    environment: Environment = load_environment(env_file=env_file)

    assert environment.database_url == "sqlite:////data/sealoc.db"
    assert environment.image_directory is None
    assert environment.config_file is None


def test_load_environment_without_database_url(tmp_path: Path) -> None:
    """load_environment() returns an Environment with database_url=None when SEALOC_DATABASE_URL is not set."""
    env_file: Path = tmp_path / ".env"
    env_file.write_text("")

    environment: Environment = load_environment(env_file=env_file)

    assert environment.database_url is None


def test_load_environment_with_optional_fields(tmp_path: Path) -> None:
    """load_environment() populates optional fields when set."""
    image_dir: Path = tmp_path / "images"
    config_file: Path = tmp_path / "config.toml"
    env_file: Path = tmp_path / ".env"
    env_file.write_text(
        f'SEALOC_DATABASE_URL="sqlite:////data/sealoc.db"\n'
        f"SEALOC_IMAGE_DIRECTORY={image_dir}\n"
        f"SEALOC_CONFIG_FILE={config_file}\n"
    )

    environment: Environment = load_environment(env_file=env_file)

    assert environment.database_url == "sqlite:////data/sealoc.db"
    assert environment.image_directory == image_dir
    assert environment.config_file == config_file
