"""
Module for downloading and parsing the SEALOC dataset contents.
"""

from __future__ import annotations

import httpx
import pandas as pd  # type: ignore[import-untyped]

from pathlib import Path
from pydantic import (
    AnyHttpUrl,
    TypeAdapter,
    ValidationError,
)

from .types import TocEntry


def download_table_of_contents(url: str, output_path: Path) -> Path:
    """
    Download a table-of-contents file from a URL to the provided path.

    Arguments
    ---------
    url: HTTP or HTTPS URL of the table-of-contents CSV.
    output_path: Local path to write the downloaded file to.

    Returns
    -------
    Resolved path of the downloaded file.
    """
    validated_url: str = _validate_url(url)

    # Resolve absolute path and create parent directory
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Download table of contents to temporary file
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        with client.stream("GET", validated_url) as response:
            response.raise_for_status()

            temp_path: Path = output_path.with_suffix(output_path.suffix + ".part")
            with temp_path.open("wb") as file_object:
                for chunk in response.iter_bytes():
                    file_object.write(chunk)

    # Replace temporary file with output path
    temp_path.replace(output_path)

    return output_path


def _validate_url(url: str) -> str:
    """
    Validate that the provided URL is a well-formed HTTP or HTTPS URL.

    Arguments
    ---------
    url: URL string to validate.

    Returns
    -------
    Validated URL string.
    """
    try:
        return str(TypeAdapter(AnyHttpUrl).validate_python(url))
    except ValidationError as exc:
        raise ValueError(f"invalid table-of-contents URL: {url}") from exc


def read_table_of_contents(path: Path) -> pd.DataFrame:
    """
    Read a table-of-contents CSV file into a data frame.

    Arguments
    ---------
    path: Path to the table-of-contents CSV file.

    Returns
    -------
    Cleaned and normalized data frame of TOC entries.
    """
    data_frame: pd.DataFrame = pd.read_csv(path, delimiter="|")

    # Drop NaN rows
    data_frame = data_frame.dropna()

    # Strip data frame columns and values
    data_frame.columns = [column.strip() for column in data_frame.columns]
    data_frame = data_frame.map(
        lambda value: value.strip() if isinstance(value, str) else value
    )

    first_column = data_frame.columns[0]
    data_frame = data_frame[
        ~data_frame[first_column].astype(str).str.fullmatch(r"-+")
    ].copy()

    data_frame["size (bytes)"] = pd.to_numeric(
        data_frame["size (bytes)"], errors="raise"
    )
    data_frame["modified_date"] = pd.to_datetime(
        data_frame["modified_date"],
        format="ISO8601",
        errors="raise",
    )

    data_frame = data_frame.rename(
        columns={
            "size (bytes)": "size_bytes",
            "fixity (md5)": "fixity_md5",
        }
    )

    return data_frame


def parse_table_of_contents(frame: pd.DataFrame) -> list[TocEntry]:
    """
    Parse the rows in a data frame as TOC entries.

    Arguments
    ---------
    frame: Data frame with columns url, filename, size_bytes, modified_date, fixity_md5.

    Returns
    -------
    List of parsed TocEntry objects.
    """
    entries: list[TocEntry] = []
    for _, row in frame.iterrows():
        entry = TocEntry(
            url=row["http_url"],
            filename=row["filename"],
            size_bytes=row["size_bytes"],
            modified_date=row["modified_date"],
            md5=row.get("fixity_md5") or None,
        )
        entries.append(entry)
    return entries
