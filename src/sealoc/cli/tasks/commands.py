"""
Commands for sealocs CLI to invoke tasks.
"""

from pathlib import Path

import click

from sealoc.tasks.download_dataset import DEFAULT_TABLE_OF_CONTENTS_URL

from .actions import (
    dispatch_download_dataset,
    dispatch_init_database,
    dispatch_populate_database,
)


@click.group()
def command_group() -> None:
    """Commands for invoking tasks through the CLI."""
    pass


@command_group.command("init-database")
@click.option("--database-url", "database_url", type=str, default=None)
@click.option("--clear", "clear_database", type=bool, is_flag=True, default=False)
def init_database(
    database_url: str | None,
    clear_database: bool,
) -> None:
    """Initializes a database with sealocs ORM tables."""
    dispatch_init_database(database_url, clear_database)


@command_group.command("populate-database")
@click.option("--database-url", "database_url", type=str, default=None)
@click.option("--input-dir", "input_dir", type=Path, required=True)
def populate_database(
    database_url: str | None,
    input_dir: Path,
) -> None:
    """Populates a database with camera data from files."""
    if not input_dir.is_dir():
        raise FileNotFoundError(f"path is not a directory: {input_dir}")

    dispatch_populate_database(database_url, input_dir)


@command_group.command("download-dataset")
@click.option("--root-dir", "root_dir", type=Path, required=True)
@click.option("--max-workers", "max_workers", type=int, default=4, show_default=True)
@click.option("--overwrite", "overwrite", is_flag=True, default=False)
@click.option(
    "--toc-url",
    "toc_url",
    type=str,
    default=DEFAULT_TABLE_OF_CONTENTS_URL,
    show_default=True,
)
@click.option(
    "--exclude",
    "exclude_patterns",
    type=str,
    multiple=True,
    help="file patterns to exclude",
)
@click.option(
    "--config",
    "config_path",
    type=Path,
    default=None,
    help="path to TOML config file with [tasks.download_dataset] section",
)
def download_dataset(
    root_dir: Path,
    max_workers: int,
    overwrite: bool,
    toc_url: str,
    exclude_patterns: tuple[str],
    config_path: Path | None,
) -> None:
    """Downloads the SEALOC dataset into the target directory."""
    dispatch_download_dataset(
        root_dir=root_dir,
        max_workers=max_workers,
        overwrite=overwrite,
        toc_url=toc_url,
        exclude_patterns=exclude_patterns,
        config_path=config_path,
    )
