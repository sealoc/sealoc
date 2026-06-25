"""Module for loading and validating the sealoc environment."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings):
    """
    Sealoc environment configuration loaded from a .env file.

    Attributes
    ----------
    database_url: SQLAlchemy database URL for the sealoc SQLite database. Optional; when
        absent, callers are responsible for raising an appropriate error.
    image_directory: Path to the sealoc image directory.
    config_file: Path to the default sealoc config file.
    """

    model_config = SettingsConfigDict(env_prefix="SEALOC_", env_file=".env")

    database_url: str | None = None
    image_directory: Path | None = None
    config_file: Path | None = None


def load_environment(env_file: Path | None = None) -> Environment:
    """
    Load and validate the sealoc environment from a .env file.

    Arguments
    ---------
    env_file: Path to the .env file to load. Defaults to the `.env` file
        specified in `Environment.model_config` if not provided.

    Returns
    -------
    Validated Environment instance.
    """
    if env_file is not None:
        return Environment(_env_file=env_file)
    return Environment()
