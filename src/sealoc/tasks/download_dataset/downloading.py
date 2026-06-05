"""
Module for downloading files.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .types import DownloadJob


def run_downloads(
    jobs: list[DownloadJob],
    max_workers: int = 4,
) -> None:
    """
    Download all pending jobs concurrently with a progress display.

    Arguments
    ---------
    jobs: Download jobs to execute.
    max_workers: Maximum number of concurrent download threads.
    """
    console = Console()

    progress = Progress(
        TextColumn("{task.fields[label]}", justify="left"),
        BarColumn(bar_width=30),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )

    with progress:
        with httpx.Client(follow_redirects=True, timeout=None) as client:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(_download_job, client, progress, job)
                    for job in jobs
                ]
                for future in futures:
                    future.result()


def _download_job(
    client: httpx.Client,
    progress: Progress,
    job: DownloadJob,
) -> None:
    """
    Download one file, update its progress bar, then move to target and run on_complete.

    Arguments
    ---------
    client: Shared HTTP client to use for the download.
    progress: Rich Progress instance to update during download.
    job: Download job describing the source URL and target path.
    """
    label = Path(job.entry.filename).name

    with client.stream("GET", job.entry.url) as response:
        response.raise_for_status()
        total: int | None = int(response.headers.get("Content-Length", 0)) or None

        task_id: TaskID = progress.add_task("download", label=label, total=total)

        tmp_path = job.cache_path.with_suffix(job.cache_path.suffix + ".part")
        tmp_path.parent.mkdir(parents=True, exist_ok=True)

        with tmp_path.open("wb") as file_object:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                file_object.write(chunk)
                progress.update(task_id, advance=len(chunk))

    job.target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.replace(job.target_path)

    if job.on_complete is not None:
        job.on_complete(job.target_path)
