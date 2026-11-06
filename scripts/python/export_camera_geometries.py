"""Export the SEALOC camera geometries as GeoJSON files.

Writes `camera_poses.geojson`, `camera_poses_prior.geojson` and
`camera_footprints.geojson` from the SEALOC dataset tables and the Renav prior
camera poses. Each camera is a master (left) camera, keyed by its SEALOC
camera ID. Timestamps are the camera trigger times from `cameras.csv`, in
ISO 8601 (UTC) with millisecond precision.

Example:
    uv run python scripts/python/export_camera_geometries.py \
        --sealoc-dir /data/exos_01/sealoc_dataset \
        --renav-dir /data/exos_01/acfr_stereo_camera_poses_v1_renav_squidle_merged \
        --output-dir /data/exos_01/sealoc_dataset/sealoc_camera_geometries
"""

import ast
import json

import click
import pandas as pd  # type: ignore[import-untyped]

from pathlib import Path
from typing import Any

from loguru import logger

type Feature = dict[str, Any]

POSE_PROPERTIES: list[str] = [
    "camera_id",
    "camera_key",
    "camera_label",
    "camera_pose_type",
    "timestamp",
    "yaw",
    "pitch",
    "roll",
]
FOOTPRINT_PROPERTIES: list[str] = [
    "camera_id",
    "camera_key",
    "camera_label",
    "timestamp",
]


@click.command()
@click.option(
    "--sealoc-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory with the SEALOC dataset CSV files.",
)
@click.option(
    "--renav-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory with the Renav stereo camera pose CSV files.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory to write the GeoJSON files to.",
)
def main(sealoc_dir: Path, renav_dir: Path, output_dir: Path) -> None:
    """Export the camera poses, prior camera poses and footprints as GeoJSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cameras: pd.DataFrame = read_master_cameras(sealoc_dir)
    camera_columns: list[str] = [
        "camera_id",
        "camera_key",
        "camera_label",
        "timestamp",
    ]

    poses: pd.DataFrame = pd.read_csv(
        sealoc_dir / "camera_poses.csv", float_precision="round_trip"
    ).merge(cameras[camera_columns], on="camera_id", how="left", validate="one_to_one")
    if poses["camera_label"].isna().any():
        raise ValueError("camera poses reference unknown master cameras")
    poses["camera_pose_type"] = "sfm_registered"
    write_feature_collection(output_dir, "camera_poses", create_point_features(poses))

    priors: pd.DataFrame = match_prior_poses(cameras, renav_dir)
    priors["camera_pose_type"] = "slam_prior"
    write_feature_collection(
        output_dir, "camera_poses_prior", create_point_features(priors)
    )

    footprints: pd.DataFrame = pd.read_csv(sealoc_dir / "camera_footprints.csv").merge(
        cameras[camera_columns], on="camera_id", how="left", validate="one_to_one"
    )
    if footprints["camera_label"].isna().any():
        raise ValueError("camera footprints reference unknown master cameras")
    write_feature_collection(
        output_dir, "camera_footprints", create_polygon_features(footprints)
    )


def read_master_cameras(sealoc_dir: Path) -> pd.DataFrame:
    """Read the master cameras with their group label, key and timestamp.

    Args:
        sealoc_dir: Directory with the SEALOC dataset CSV files.

    Returns:
        Master cameras with `camera_id`, `camera_key`, `camera_label`,
        `timestamp` and `camera_group_label` columns.
    """
    cameras: pd.DataFrame = pd.read_csv(
        sealoc_dir / "cameras.csv",
        usecols=[
            "camera_id",
            "camera_label",
            "meta",
            "camera_group_id",
            "master_camera_id",
        ],
    )
    groups: pd.DataFrame = pd.read_csv(
        sealoc_dir / "camera_groups.csv",
        usecols=["camera_group_id", "camera_group_label"],
    )
    trigger_times: pd.Series = cameras["meta"].map(
        lambda meta: ast.literal_eval(meta)["trigger_time"]
    )
    cameras["timestamp"] = format_timestamps(trigger_times)
    cameras["camera_key"] = cameras["camera_label"]
    masters: pd.DataFrame = cameras[cameras["master_camera_id"].isna()]
    return masters.merge(groups, on="camera_group_id")


def format_timestamps(unix_seconds: pd.Series) -> pd.Series:
    """Format Unix times as ISO 8601 (UTC) strings with millisecond precision.

    Rounding to whole milliseconds carries into the next second, so QGIS never
    sees a fractional second that rounds up to 1000 ms.

    Args:
        unix_seconds: Unix times in seconds.

    Returns:
        Timestamps such as `2009-06-12T23:22:25.000+00:00`.
    """
    milliseconds: pd.Series = (unix_seconds * 1e3).round().astype("int64")
    datetimes: pd.Series = pd.to_datetime(milliseconds, unit="ms", utc=True)
    return datetimes.dt.strftime("%Y-%m-%dT%H:%M:%S.%f").str[:-3] + "+00:00"


def match_prior_poses(cameras: pd.DataFrame, renav_dir: Path) -> pd.DataFrame:
    """Match the master cameras to their Renav prior poses.

    Each camera is matched by label against `stereo_left_label` in the Renav
    file of its own camera group.

    Args:
        cameras: Master cameras from `read_master_cameras`.
        renav_dir: Directory with the Renav stereo camera pose CSV files.

    Returns:
        Master cameras with the Renav pose columns, and `heading` renamed to
        `yaw`.

    Raises:
        ValueError: If a Renav file has duplicate labels or a camera has no
            matching Renav pose.
    """
    frames: list[pd.DataFrame] = []
    for group_label, group_cameras in cameras.groupby("camera_group_label"):
        renav: pd.DataFrame = pd.read_csv(
            renav_dir / f"{group_label}_stereo_camera_poses_renav.csv",
            float_precision="round_trip",
        ).drop(columns=["timestamp"])
        if renav["stereo_left_label"].duplicated().any():
            raise ValueError(f"duplicate Renav labels in {group_label}")
        frames.append(
            group_cameras.merge(
                renav,
                left_on="camera_label",
                right_on="stereo_left_label",
                how="left",
                validate="one_to_one",
            )
        )

    priors: pd.DataFrame = pd.concat(frames)
    if priors["stereo_left_label"].isna().any():
        raise ValueError("some cameras have no matching Renav pose")
    return priors.rename(columns={"heading": "yaw"})


def create_point_features(poses: pd.DataFrame) -> list[Feature]:
    """Create 3D point features from camera poses, sorted by camera ID.

    Args:
        poses: Camera poses with the pose properties and coordinate columns.

    Returns:
        GeoJSON point features.
    """
    return [
        {
            "type": "Feature",
            "properties": {name: row[name] for name in POSE_PROPERTIES},
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"], row["height"]],
            },
        }
        for row in poses.sort_values("camera_id").to_dict("records")
    ]


def create_polygon_features(footprints: pd.DataFrame) -> list[Feature]:
    """Create 3D polygon features from camera footprints, sorted by camera ID.

    Args:
        footprints: Camera footprints with the footprint properties and a
            `coordinates` column of Python literal strings.

    Returns:
        GeoJSON polygon features.
    """
    return [
        {
            "type": "Feature",
            "properties": {name: row[name] for name in FOOTPRINT_PROPERTIES},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [list(point) for point in ast.literal_eval(row["coordinates"])]
                ],
            },
        }
        for row in footprints.sort_values("camera_id").to_dict("records")
    ]


def write_feature_collection(
    output_dir: Path, name: str, features: list[Feature]
) -> None:
    """Write features as a CRS84 GeoJSON feature collection.

    Args:
        output_dir: Directory to write the file to.
        name: Collection name, also used as the file stem.
        features: GeoJSON features.
    """
    collection: dict[str, Any] = {
        "type": "FeatureCollection",
        "name": name,
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": features,
    }
    (output_dir / f"{name}.geojson").write_text(json.dumps(collection))
    logger.info(f"Wrote {len(features)} features to {name}.geojson")


if __name__ == "__main__":
    main()
