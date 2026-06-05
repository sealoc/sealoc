"""
TOML config loader for the download dataset task.
"""

import msgspec.toml

from pathlib import Path

from .types import (
    DEFAULT_DOWNLOAD_CONFIG,
    DownloadDatasetConfig,
)


def load_download_config(path: Path) -> DownloadDatasetConfig:
    """
    Load DownloadDatasetConfig from the [tasks.download_dataset] section of a TOML file.

    Arguments
    ---------
    path: Path to the TOML config file.

    Returns
    -------
    Parsed DownloadDatasetConfig, or DEFAULT_DOWNLOAD_CONFIG if the section is absent.
    """
    raw: dict = msgspec.toml.decode(path.read_bytes())
    section: dict = raw.get("tasks", {}).get("download_dataset", {})
    if not section:
        return DEFAULT_DOWNLOAD_CONFIG
    return DownloadDatasetConfig.model_validate(section)
