# SEALOC - A Benchmark Dataset for Long-Term Visual Localization in Dynamic Benthic Environments

![ubuntu](https://github.com/sealoc/sealoc/actions/workflows/ubuntu.yml/badge.svg)
![windows](https://github.com/sealoc/sealoc/actions/workflows/windows.yml/badge.svg)
![macos](https://github.com/sealoc/sealoc/actions/workflows/macos.yml/badge.svg)
[![Dataset](https://img.shields.io/badge/Dataset-10.11582%2F2026.QRO1LF3Z-blue)](https://doi.org/10.11582/2026.QRO1LF3Z)
[![Paper](https://img.shields.io/badge/Paper-10.3389%2Ffrobt.2026.1821019-blue)](https://doi.org/10.3389/frobt.2026.1821019)

SEALOC is a benchmark dataset and Python library for long-term visual localization in
dynamic benthic (underwater) environments. The library provides tools for downloading
the dataset and querying camera geometry data (poses, footprints, calibrations).

## Documentation

- [Getting Started](docs/01_getting_started.md) — install, download the dataset, and run your first query
- [Usage](docs/02_usage.md) — practical examples for querying bundles, calibrations, poses, and spatial indices
- [Data Model](docs/03_data_model.md) — bundles, groups, cameras, poses, and footprints explained
- [API Reference](docs/04_api_reference.md) — full reference for `DataAccessLayer`, repositories, and geometry indices

## Quick start

Install the library directly from GitHub:

**uv** (recommended):
```shell
uv add git+https://github.com/sealoc/sealoc.git
```

**pip**:
```shell
pip install git+https://github.com/sealoc/sealoc.git
```

See the [Getting Started guide](docs/01_getting_started.md) for how to download the
dataset and run your first query.

## Examples

### Example 1 - Create the data access layer

```python
from pathlib import Path
from sealoc.dal import create_data_access_layer, DataAccessLayer

dal: DataAccessLayer = create_data_access_layer(
    database_url="sqlite:////data/sealoc/sealoc.db",
    image_dir=Path("/data/sealoc/sealoc_images_raw"),
)
```

### Example 2 - Load a camera bundle and its groups

```python
from sealoc.models import Camera, CameraBundle, CameraGroup

with dal.session() as repos:
    # Fetch a specific bundle by label
    bundle: CameraBundle | None = repos.bundles.get_one_by(label="survey_2023")

    # The bundle contains one or more camera groups (e.g. individual dives)
    groups: list[CameraGroup] = list(bundle.groups)
    group_a: CameraGroup = groups[0]
    group_b: CameraGroup = groups[1]

    # Each group holds its own set of cameras
    cameras_a: list[Camera] = list(group_a.cameras)
    cameras_b: list[Camera] = list(group_b.cameras)
```

### Example 3 - Access sensor, pose, and footprint for a camera

```python
from sealoc.models import Camera, CameraCalibration, CameraFootprint, CameraPose, CameraSensor

camera: Camera = cameras[0]

# The camera sensor and calibration are always present
sensor: CameraSensor = camera.sensor
calibration: CameraCalibration = sensor.calibration

# The pose and footprint are optional — guard with has_pose() / has_footprint() first
if camera.has_pose():
    pose: CameraPose = camera.get_pose()

if camera.has_footprint():
    footprint: CameraFootprint = camera.get_footprint()
```

### Example 4 - Master and slave cameras in a stereo rig

```python
from sealoc.transforms import RigidTransform

with dal.session() as repos:
    group: CameraGroup = repos.groups.get_one_by(label="stereo_2023")

    # Separate master and slave cameras within the group
    master_cameras: list[Camera] = [camera for camera in group.cameras if camera.is_master]
    slave_cameras: list[Camera] = [camera for camera in group.cameras if camera.is_slave]

    # Each slave camera holds a reference to its master
    for slave in slave_cameras:
        master: Camera | None = slave.master_camera

        # The slave sensor extrinsics are expressed relative to the master
        transform: RigidTransform = slave.sensor.transform
```

### Example 5 - Load an image and convert it to NumPy or PyTorch

```python
import numpy as np
import torch

from sealoc.image import Image
from sealoc.models import Camera, CameraBundle

with dal.session() as repos:
    bundle: CameraBundle | None = repos.bundles.get_one_by(label="survey_2023")

    if bundle is not None and dal.image_store is not None:
        for camera in bundle.cameras:
            if dal.image_store.has_image(camera.image_label):
                image: Image = dal.image_store.load_image(camera.image_label)

                # Layout and pixel format
                print(image.layout)        # ImageLayout(height=..., width=..., channels=...)
                print(image.pixel_format)  # ImagePixelFormat.RGB

                # Convert to NumPy or PyTorch
                array: np.ndarray = image.to_numpy()
                tensor = torch.from_numpy(array)
```

Additional examples covering spatial indices can be found in the
[Usage guide](docs/02_usage.md).

## Citation

If you use the `sealoc` library or dataset in your research, please cite the following works:

**Dataset**

```bibtex
@misc{larsen_sealoc_2026,
  title        = {{SEALOC}: A Benchmark Dataset for Long-Term Visual Localization in Dynamic Benthic Environments},
  author       = {Larsen, Martin Kvisvik},
  collaborator = {Pizarro, Oscar},
  year         = {2026},
  publisher    = {NIRD RDA},
  doi          = {10.11582/2026.QRO1LF3Z},
  url          = {https://archive.sigma2.no/dataset/sealoc},
  language     = {en},
  keywords     = {AI, AUV, Benthic Imaging, Computer Vision, Environmental Monitoring, Robotics},
}
```

**Paper**

```bibtex
@article{larsen_long-term_2026,
  title        = {Long-term visual localization in dynamic benthic environments: the {SEALOC} dataset, footprint-based ground truth, and visual place recognition benchmark},
  shorttitle   = {Long-Term Visual Localization in Dynamic Benthic Environments},
  author       = {Larsen, Martin Kvisvik and Pizarro, Oscar},
  year         = {2026},
  month        = june,
  journal      = {Frontiers in Robotics and {AI}},
  volume       = {13},
  pages        = {1821019},
  doi          = {10.3389/frobt.2026.1821019},
  url          = {https://www.frontiersin.org/articles/10.3389/frobt.2026.1821019/full},
}
```
