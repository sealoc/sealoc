"""Convert the SEALOC camera geometry GeoJSON files to CSV files.

Reads `camera_poses.geojson`, `camera_poses_prior.geojson` and
`camera_footprints.geojson` from a directory, as written by
`export_camera_geometries.py`, and writes a CSV file next to each. Each CSV
file has the feature properties as columns, the geometry as coordinate
columns, and an `srid` column.

Example:
    uv run python scripts/python/convert_camera_geometries_to_csv.py \
        --directory /data/exos_01/sealoc_dataset/sealoc_camera_geometries
"""

import json

import click
import pandas as pd  # type: ignore[import-untyped]

from pathlib import Path
from typing import Any

from loguru import logger

type Feature = dict[str, Any]

SRID: int = 4326


@click.command()
@click.option(
    "--directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory with the GeoJSON files; the CSV files are written here.",
)
def main(directory: Path) -> None:
    """Convert the camera geometry GeoJSON files to CSV files."""
    for name in ["camera_poses", "camera_poses_prior"]:
        rows: list[dict[str, Any]] = [
            convert_pose_feature(feature) for feature in read_features(directory, name)
        ]
        write_rows(directory, name, rows)

    footprint_rows: list[dict[str, Any]] = [
        convert_footprint_feature(feature)
        for feature in read_features(directory, "camera_footprints")
    ]
    write_rows(directory, "camera_footprints", footprint_rows)


def read_features(directory: Path, name: str) -> list[Feature]:
    """Read the features of a GeoJSON file.

    Args:
        directory: Directory with the GeoJSON file.
        name: File stem of the GeoJSON file.

    Returns:
        GeoJSON features.
    """
    collection: dict[str, Any] = json.loads((directory / f"{name}.geojson").read_text())
    return collection["features"]


def convert_pose_feature(feature: Feature) -> dict[str, Any]:
    """Convert a camera pose point feature to a CSV row.

    Args:
        feature: GeoJSON point feature.

    Returns:
        Row with the columns of the camera pose CSV files.
    """
    properties: dict[str, Any] = feature["properties"]
    longitude, latitude, height = feature["geometry"]["coordinates"]
    return {
        "camera_id": properties["camera_id"],
        "camera_key": properties["camera_key"],
        "camera_label": properties["camera_label"],
        "camera_pose_type": properties["camera_pose_type"],
        "timestamp": properties["timestamp"],
        "srid": SRID,
        "longitude": longitude,
        "latitude": latitude,
        "height": height,
        "yaw": properties["yaw"],
        "pitch": properties["pitch"],
        "roll": properties["roll"],
    }


def convert_footprint_feature(feature: Feature) -> dict[str, Any]:
    """Convert a camera footprint polygon feature to a CSV row.

    The coordinates are written as a Python literal list of
    `(longitude, latitude, height)` tuples, as in the published dataset.

    Args:
        feature: GeoJSON polygon feature.

    Returns:
        Row with the columns of the camera footprint CSV file.
    """
    properties: dict[str, Any] = feature["properties"]
    (ring,) = feature["geometry"]["coordinates"]
    return {
        "camera_id": properties["camera_id"],
        "camera_key": properties["camera_key"],
        "camera_label": properties["camera_label"],
        "timestamp": properties["timestamp"],
        "srid": SRID,
        "coordinates": str([tuple(point) for point in ring]),
    }


def write_rows(directory: Path, name: str, rows: list[dict[str, Any]]) -> None:
    """Write rows to a CSV file.

    Args:
        directory: Directory to write the file to.
        name: File stem of the CSV file.
        rows: Rows to write.
    """
    pd.DataFrame(rows).to_csv(directory / f"{name}.csv", index=False)
    logger.info(f"Wrote {len(rows)} rows to {name}.csv")


if __name__ == "__main__":
    main()
