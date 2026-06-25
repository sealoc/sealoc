# Getting Started

Install the library directly from GitHub:

**uv** (recommended):
```shell
uv add git+https://github.com/sealoc/sealoc.git
```

**pip**:
```shell
pip install git+https://github.com/sealoc/sealoc.git
```

## Download the dataset

Use the Python API to download all dataset files to a local directory:

```python
from pathlib import Path
from sealoc.tasks.download_dataset import (
    DownloadDatasetCommand,
    DEFAULT_TABLE_OF_CONTENTS_URL,
    run_download_dataset,
)

command: DownloadDatasetCommand = DownloadDatasetCommand(
    toc_url=DEFAULT_TABLE_OF_CONTENTS_URL,
    root_dir=Path("/data/sealoc"),
)
run_download_dataset(command)
```

This downloads the SQLite database and image archives. Files are placed according to
these routing rules:

| File pattern                | Destination                           |
|-----------------------------|---------------------------------------|
| `*.db`, `*.sqlite`, `*.csv` | `<root-dir>/`                         |
| `*_images_raw.zip`          | `<root-dir>/sealoc_images_raw/`       |
| `*_images_grayworld.zip`    | `<root-dir>/sealoc_images_grayworld/` |

After downloading, unzip the image archives if you plan to load images.

`DownloadDatasetCommand` accepts a few optional arguments:

| Argument                | Default | Description                                      |
|-------------------------|---------|--------------------------------------------------|
| `max_workers`           | `4`     | Number of concurrent download workers            |
| `overwrite`             | `False` | Re-download files that already exist on disk     |
| `extra_exclude_patterns`| `[]`    | Glob patterns for files to skip (e.g. `["*_images_grayworld.zip"]`) |

### Alternative: CLI

If you are working from the source repository, the `sealoc` CLI is also available:

```shell
uv run sealoc tasks download-dataset --root-dir /data/sealoc
```

## Query data

With a `.env` file configured, create a `DataAccessLayer` and open a session to query
camera data:

```python
from sealoc.dal import load_data_access_layer, DataAccessLayer
from sealoc.models import Camera, CameraBundle, CameraPose

dal: DataAccessLayer = load_data_access_layer()

with dal.session() as repos:
    bundle_ids: set[int] = repos.bundles.get_all_ids()
    bundle: CameraBundle | None = repos.bundles.get_one_by(label="survey_2023")
    cameras: list[Camera] = bundle.cameras
    poses: list[CameraPose] = [
        camera.get_pose() for camera in cameras if camera.has_pose()
    ]
```

You can also pass `database_url` and `image_dir` explicitly to override the environment:

```python
dal: DataAccessLayer = load_data_access_layer(
    database_url="sqlite:////data/sealoc/sealoc.db",
    image_dir="/data/sealoc/sealoc_images_raw",
)
```

See [Usage](02_usage.md) for practical examples, [Data Model](03_data_model.md) for an
explanation of how bundles, groups, cameras, poses and footprints relate to each other,
and [API Reference](04_api_reference.md) for the full method listings.
