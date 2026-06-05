"""
Module for routing and planning dataset downloads.
"""

import shutil
import zipfile

from fnmatch import fnmatch
from pathlib import Path

from .types import (
    DownloadDatasetConfig,
    DownloadJob,
    DownloadPlan,
    TocEntry,
)


def route_entry(entry: TocEntry, config: DownloadDatasetConfig) -> Path:
    """
    Return the destination subdirectory for a TOC entry (relative to root_dir).

    Arguments
    ---------
    entry: TOC entry to route.
    config: Download config with routing rules and default destination.

    Returns
    -------
    Relative destination path for the entry.
    """
    name = Path(entry.filename).name.lower()
    for rule in config.routing_rules:
        if any(fnmatch(name, pattern.lower()) for pattern in rule.patterns):
            return rule.destination
    return config.default_destination


def build_download_job(
    entry: TocEntry,
    destination: Path,
    root_dir: Path,
    cache_dir: Path,
    overwrite: bool,
) -> DownloadJob:
    """
    Build a DownloadJob for a single TOC entry.

    Arguments
    ---------
    entry: TOC entry to build a job for.
    destination: Relative destination directory under root_dir.
    root_dir: Root download directory.
    cache_dir: Temporary cache directory for in-progress downloads.
    overwrite: Whether to overwrite an existing target file.

    Returns
    -------
    Configured DownloadJob for the entry.
    """
    cache_path = cache_dir / Path(entry.filename).name
    target_path = root_dir / destination / Path(entry.filename).name

    skip = target_path.exists() and not overwrite
    on_complete = _zip_on_complete if entry.filename.lower().endswith(".zip") else None

    return DownloadJob(
        entry=entry,
        cache_path=cache_path,
        target_path=target_path,
        skip=skip,
        on_complete=on_complete,
    )


def build_download_plan(
    entries: list[TocEntry],
    config: DownloadDatasetConfig,
    root_dir: Path,
    cache_dir: Path,
    overwrite: bool,
) -> DownloadPlan:
    """
    Build a DownloadPlan by routing each entry and constructing its job.

    Arguments
    ---------
    entries: TOC entries to include in the plan.
    config: Download config with routing rules.
    root_dir: Root download directory.
    cache_dir: Temporary cache directory for in-progress downloads.
    overwrite: Whether to overwrite existing target files.

    Returns
    -------
    DownloadPlan with a job for each entry.
    """
    jobs: list[DownloadJob] = []
    for entry in entries:
        destination = route_entry(entry, config)
        job = build_download_job(entry, destination, root_dir, cache_dir, overwrite)
        jobs.append(job)
    return DownloadPlan(jobs=jobs)


def validate_download_plan(plan: DownloadPlan, root_dir: Path) -> None:
    """
    Validate that there is sufficient disk space for a download plan.

    Arguments
    ---------
    plan: Download plan to validate.
    root_dir: Root directory to check for available disk space.
    """
    required = plan.total_bytes
    free = shutil.disk_usage(root_dir).free
    if required > free:
        raise OSError(
            28,
            f"No space left on device (required={required}, free={free})",
            str(root_dir),
        )


def _zip_on_complete(path: Path) -> None:
    """
    Extract a zip archive next to the zip file, then delete it.

    If all entries share a single top-level directory, extract directly into
    path.parent so that directory becomes the final path component. Otherwise
    wrap the contents in a new directory named after the zip stem.

    Arguments
    ---------
    path: Path to the downloaded zip file.
    """
    with zipfile.ZipFile(path) as zip_file:
        top_level = _zip_single_top_level_dir(zip_file)
        extract_dir = path.parent if top_level is not None else path.parent / path.stem
        extract_dir.mkdir(parents=True, exist_ok=True)
        zip_file.extractall(extract_dir)
    path.unlink()


def _zip_single_top_level_dir(zip_file: zipfile.ZipFile) -> str | None:
    """
    Return the single top-level directory if every entry in the zip shares one.

    Arguments
    ---------
    zip_file: Open ZipFile to inspect.

    Returns
    -------
    Top-level directory name, or None if entries span multiple roots.
    """
    names = zip_file.namelist()
    if not names:
        return None
    top_levels = {name.split("/")[0] for name in names}
    if len(top_levels) != 1:
        return None
    top_level = top_levels.pop()
    # Confirm it is a directory prefix, not a lone root-level file
    if any(name.startswith(top_level + "/") for name in names):
        return top_level
    return None
