"""
Task for downloading the SEALOC dataset.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from .downloading import run_downloads
from .planning import (
    build_download_plan,
    validate_download_plan,
)
from .table_of_contents import (
    download_table_of_contents,
    parse_table_of_contents,
    read_table_of_contents,
)
from .types import (
    DownloadDatasetCommand,
    DownloadPlan,
    TocEntry,
)


def run_download_dataset(command: DownloadDatasetCommand) -> None:
    """
    Download the SEALOC dataset into the requested root directory.

    Arguments
    ---------
    command: Command describing the download URL, destination, and options.
    """
    root_dir: Path = command.root_dir
    cache_dir: Path = root_dir / ".cache"

    root_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    toc_path: Path = cache_dir / "table_of_contents.csv"
    toc_path = download_table_of_contents(url=command.toc_url, output_path=toc_path)

    entries: list[TocEntry] = parse_table_of_contents(read_table_of_contents(toc_path))
    entries = _filter_entries(entries, command.exclude_patterns)

    plan: DownloadPlan = build_download_plan(
        entries=entries,
        config=command.config,
        root_dir=root_dir,
        cache_dir=cache_dir,
        overwrite=command.overwrite,
    )

    validate_download_plan(plan, root_dir)
    run_downloads(plan.pending, max_workers=command.max_workers)


def _filter_entries(
    entries: list[TocEntry], exclude_patterns: list[str]
) -> list[TocEntry]:
    """
    Filter out entries whose filename matches any exclude pattern.

    Arguments
    ---------
    entries: TOC entries to filter.
    exclude_patterns: Glob patterns to match against filenames.

    Returns
    -------
    Entries whose filenames do not match any exclude pattern.
    """
    if not exclude_patterns:
        return entries

    filtered: list[TocEntry] = []
    for entry in entries:
        name = Path(entry.filename).name.lower()
        if not any(fnmatch(name, pattern.lower()) for pattern in exclude_patterns):
            filtered.append(entry)
    return filtered
