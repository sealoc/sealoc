"""
Data types for dataset download task.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import (
    dataclass,
    field,
)
from datetime import datetime
from pathlib import Path

from pydantic import (
    BaseModel,
    Field,
)


class TocEntry(BaseModel):
    """
    A parsed file entry from the dataset table of contents.

    Attributes
    ----------
    url: Download URL for the file.
    filename: Name of the file.
    size_bytes: File size in bytes.
    modified_date: Last modified timestamp.
    md5: Optional MD5 checksum.
    """

    url: str
    filename: str
    size_bytes: int
    modified_date: datetime
    md5: str | None = None


class RoutingRule(BaseModel):
    """
    A pattern-to-destination mapping for routing TOC entries to subdirectories.

    Attributes
    ----------
    patterns: Glob patterns to match against filenames.
    destination: Relative destination path under the root directory.
    """

    patterns: list[str]
    destination: Path  # relative to root_dir


class DownloadDatasetConfig(BaseModel):
    """
    Stable, project-level configuration for the download dataset task.

    Attributes
    ----------
    routing_rules: Rules for routing files to subdirectories.
    default_destination: Destination for files that match no routing rule.
    exclude_patterns: Glob patterns for files to exclude from the download.
    """

    routing_rules: list[RoutingRule] = Field(default_factory=list)
    default_destination: Path = Path(".")
    exclude_patterns: list[str] = Field(default_factory=list)


DEFAULT_DOWNLOAD_CONFIG = DownloadDatasetConfig(
    routing_rules=[
        RoutingRule(
            patterns=["*_images_raw.zip"],
            destination=Path("sealoc_images_raw"),
        ),
        RoutingRule(
            patterns=["*_images_grayworld.zip"],
            destination=Path("sealoc_images_grayworld"),
        ),
        RoutingRule(
            patterns=["*.csv", "*.db", "*.sqlite"],
            destination=Path("."),
        ),
    ]
)


class DownloadDatasetCommand(BaseModel):
    """
    Command type for downloading the SEALOC dataset.

    Attributes
    ----------
    toc_url: URL of the dataset table-of-contents CSV.
    root_dir: Root directory to download files into.
    overwrite: Whether to overwrite existing files.
    max_workers: Maximum number of concurrent download workers.
    extra_exclude_patterns: Additional filename patterns to exclude.
    config: Download configuration with routing rules.
    """

    toc_url: str
    root_dir: Path
    overwrite: bool = False
    max_workers: int = 4
    extra_exclude_patterns: list[str] = Field(default_factory=list)
    config: DownloadDatasetConfig = Field(
        default_factory=lambda: DEFAULT_DOWNLOAD_CONFIG
    )

    @property
    def exclude_patterns(self) -> list[str]:
        """
        Return the combined list of exclude patterns.

        Returns
        -------
        Config exclude patterns merged with extra_exclude_patterns.
        """
        return self.config.exclude_patterns + self.extra_exclude_patterns


@dataclass
class DownloadJob:
    """
    A resolved file to download.

    Attributes
    ----------
    entry: TOC entry for the file to download.
    cache_path: Temporary cache path during download.
    target_path: Final destination path after download.
    skip: Whether to skip this job (file already exists).
    on_complete: Optional callback to run after the file is downloaded.
    """

    entry: TocEntry
    cache_path: Path
    target_path: Path
    skip: bool
    on_complete: Callable[[Path], None] | None = field(default=None)


@dataclass
class DownloadPlan:
    """
    Resolved dataset download plan.

    Attributes
    ----------
    jobs: All download jobs in the plan, including skipped ones.
    """

    jobs: list[DownloadJob] = field(default_factory=list)

    @property
    def pending(self) -> list[DownloadJob]:
        """
        Return jobs that are not marked as skipped.

        Returns
        -------
        List of download jobs to execute.
        """
        return [job for job in self.jobs if not job.skip]

    @property
    def total_bytes(self) -> int:
        """
        Return the total download size of pending jobs.

        Returns
        -------
        Sum of size_bytes for all pending jobs.
        """
        return sum(job.entry.size_bytes for job in self.pending)
