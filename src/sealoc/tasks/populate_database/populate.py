"""
Module for running a database population task.
"""

import ast

import pandas as pd  # type: ignore[import-untyped]

import sealoc.database as db

from pathlib import Path

from .builders import build_records_from_tables
from .types import (
    CameraDataTables,
    PopulateDatabaseCommand,
    PopulateDatabaseContext,
    PopulateDatabaseState,
)

CAMERA_FILENAMES: list[str] = [
    "camera_poses.csv",
    "camera_bundles.csv",
    "camera_groups.csv",
    "cameras.csv",
    "camera_footprints.csv",
    "camera_calibrations.csv",
    "camera_sensors.csv",
]


def run_populate_database(command: PopulateDatabaseCommand) -> None:
    """
    Populate a database with camera data from files.

    Arguments
    ---------
    command: Command containing the database URL and input directory.
    """
    context: PopulateDatabaseContext = PopulateDatabaseContext()

    # Create engine from database URL
    engine: db.Engine = db.create_engine(url=command.database_url)

    _check_camera_table_files(command.input_dir)
    context.camera_tables = _read_camera_tables(command.input_dir)
    _parse_table_columns(context.camera_tables)

    with db.session_scope(engine) as session:
        # NOTE: Temporary - adding session to model builders
        _state: PopulateDatabaseState = build_records_from_tables(
            session, context.camera_tables
        )


def _check_camera_table_files(input_dir: Path) -> None:
    """
    Check that all expected CSV files are present in the directory.

    Arguments
    ---------
    input_dir: Directory to check for camera CSV files.
    """
    listed_filepaths: list[Path] = [
        entry for entry in input_dir.iterdir() if entry.is_file()
    ]
    listed_filenames: list[str] = [path.name for path in listed_filepaths]

    for filename in CAMERA_FILENAMES:
        if filename not in listed_filenames:
            raise FileNotFoundError(f"missing expected camera file: {filename}")


def _read_camera_tables(input_dir: Path) -> CameraDataTables:
    """
    Read all camera CSV files from a directory into a CameraDataTables object.

    Arguments
    ---------
    input_dir: Directory containing the camera CSV files.

    Returns
    -------
    CameraDataTables populated from the CSV files.
    """
    listed_filepaths: list[Path] = [
        entry for entry in input_dir.iterdir() if entry.is_file()
    ]
    camera_filepaths: list[Path] = [
        path for path in listed_filepaths if path.name in CAMERA_FILENAMES
    ]

    camera_data_frames: dict[str, pd.DataFrame] = {
        filepath.stem: pd.read_csv(filepath) for filepath in camera_filepaths
    }

    return CameraDataTables(**camera_data_frames)


def _parse_table_columns(tables: CameraDataTables) -> None:
    """
    Parse stringified tuple/dict columns in-place using ast.literal_eval.

    Arguments
    ---------
    tables: Camera data tables whose columns contain Python literal strings.
    """
    # Evaluate the sensor location and rotation strings as tuples
    tables.camera_sensors["sensor_location"] = tables.camera_sensors[
        "sensor_location"
    ].apply(ast.literal_eval)
    tables.camera_sensors["sensor_rotation"] = tables.camera_sensors[
        "sensor_rotation"
    ].apply(ast.literal_eval)
    tables.camera_footprints["coordinates"] = tables.camera_footprints[
        "coordinates"
    ].apply(ast.literal_eval)

    tables.cameras["meta"] = tables.cameras["meta"].apply(ast.literal_eval)
    tables.camera_groups["meta"] = tables.camera_groups["meta"].apply(ast.literal_eval)
    tables.camera_bundles["meta"] = tables.camera_bundles["meta"].apply(
        ast.literal_eval
    )
