"""
Actions for invoking sealocs tasks through the CLI.
"""

from pathlib import Path

from sealoc.environment import load_environment
from sealoc.tasks.download_dataset import (
    DEFAULT_DOWNLOAD_CONFIG,
    DownloadDatasetCommand,
    load_download_config,
    run_download_dataset,
)
from sealoc.tasks.populate_database import (
    InitializeDatabaseCommand,
    PopulateDatabaseCommand,
    run_init_database,
    run_populate_database,
)


def dispatch_init_database(
    database_url: str | None,
    clear_database: bool,
) -> None:
    """
    Dispatch a task to initialize a database.

    Arguments
    ---------
    database_url: Database URL string. Falls back to the SEALOC_DATABASE_URL env var.
    clear_database: Whether to drop existing tables before creating new ones.
    """
    resolved_url: str | None = database_url or load_environment().database_url
    if resolved_url is None:
        raise ValueError(
            "No database URL provided. Pass --database-url explicitly or set SEALOC_DATABASE_URL."
        )
    command: InitializeDatabaseCommand = InitializeDatabaseCommand(
        database_url=resolved_url,
        clear_database=clear_database,
    )
    run_init_database(command)


def dispatch_populate_database(
    database_url: str | None,
    input_dir: Path,
) -> None:
    """
    Dispatch a task to populate a database from files.

    Arguments
    ---------
    database_url: Database URL string. Falls back to the SEALOC_DATABASE_URL env var.
    input_dir: Directory containing the camera CSV files.
    """
    resolved_url: str | None = database_url or load_environment().database_url
    if resolved_url is None:
        raise ValueError(
            "No database URL provided. Pass --database-url explicitly or set SEALOC_DATABASE_URL."
        )
    command: PopulateDatabaseCommand = PopulateDatabaseCommand(
        database_url=resolved_url,
        input_dir=input_dir,
    )
    run_populate_database(command)


def dispatch_download_dataset(
    root_dir: Path,
    max_workers: int,
    overwrite: bool,
    toc_url: str,
    exclude_patterns: tuple[str],
    config_path: Path | None,
) -> None:
    """
    Dispatch a task to download the SEALOC dataset.

    Arguments
    ---------
    root_dir: Root directory to download files into.
    max_workers: Maximum number of concurrent download workers.
    overwrite: Whether to overwrite existing files.
    toc_url: URL of the dataset table-of-contents CSV.
    exclude_patterns: Filename patterns to exclude from the download.
    config_path: Path to a TOML config file with routing rules.
    """
    config = (
        load_download_config(config_path) if config_path else DEFAULT_DOWNLOAD_CONFIG
    )
    command: DownloadDatasetCommand = DownloadDatasetCommand(
        root_dir=root_dir,
        max_workers=max_workers,
        overwrite=overwrite,
        toc_url=toc_url,
        extra_exclude_patterns=list(exclude_patterns),
        config=config,
    )
    run_download_dataset(command)
