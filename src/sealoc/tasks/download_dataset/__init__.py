"""
Package for downloading the SEALOC dataset.
"""

from .config import load_download_config as load_download_config
from .runner import run_download_dataset as run_download_dataset
from .types import (
    DEFAULT_DOWNLOAD_CONFIG as DEFAULT_DOWNLOAD_CONFIG,
    DownloadDatasetCommand as DownloadDatasetCommand,
    DownloadDatasetConfig as DownloadDatasetConfig,
)

DEFAULT_TABLE_OF_CONTENTS_URL: str = (
    "https://data.archive.sigma2.no/dataset/"
    "24978c88-334f-4024-b726-fe64e8704046/download/"
    "table_of_contents_10.11582_2026.qro1lf3z.csv"
)

__all__ = []
