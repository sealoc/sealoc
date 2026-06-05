# Usage

This page walks through practical examples for querying the SEALOC dataset. All
examples assume you have already downloaded the dataset and populated the database.
See [Getting Started](01_getting_started.md) if you haven't done that yet.

## Setting up the data access layer

`create_data_access_layer` is the entry point for all queries. Pass the path to your
SQLite database and, optionally, the directory containing the unpacked image archives.

```python
from pathlib import Path

from sealoc.dal import create_data_access_layer, DataAccessLayer

dal: DataAccessLayer = create_data_access_layer(
    database_url="sqlite:////data/sealoc/sealoc.db",
    image_dir=Path("/data/sealoc/sealoc_images_raw"),
)
```

If you have a `.env` file with `SEALOC_DB_URL` set, you can omit `database_url` and it
will be picked up automatically. `image_dir` is always optional — `dal.image_store` will be
`None` if you skip it.

All database queries happen inside a `dal.session()` context manager. The session
commits on success and rolls back on exception.

---

## Data model hierarchy

`CameraBundle` is the top-level container. It holds one or more `CameraGroup` objects,
each of which holds a set of `Camera` objects. Each camera links to a `CameraSensor` and
optionally to a `CameraPose` and `CameraFootprint`.

```python
from sealoc.models import (
    Camera,
    CameraBundle,
    CameraFootprint,
    CameraGroup,
    CameraPose,
    CameraSensor,
)

with dal.session() as repos:
    bundle: CameraBundle | None = repos.bundles.get_one_by(label="survey_2023")

if bundle is None:
    raise RuntimeError("bundle not found")

# Bundle-level metadata
print(bundle.label, bundle.meta)

group: CameraGroup = next(iter(bundle.groups))

# Group-level metadata
print(group.label, group.meta)

camera: Camera = next(iter(group.cameras))

# Camera-level metadata
print(camera.label, camera.meta)

# Every camera has a sensor (carries the calibration)
sensor: CameraSensor = camera.sensor

# In a stereo rig, slave cameras point back to their master
if camera.is_slave and camera.master_camera is not None:
    master: Camera = camera.master_camera
    print(f"slave {camera.label} → master {master.label}")

# Pose and footprint are optional — guard before accessing
if camera.has_pose():
    pose: CameraPose = camera.get_pose()
    print(f"position: {pose.location}  CRS: {pose.epsg_string}")
    print(f"yaw={pose.yaw:.1f}  pitch={pose.pitch:.1f}  roll={pose.roll:.1f}")

if camera.has_footprint():
    footprint: CameraFootprint = camera.get_footprint()
    print(f"centroid: {footprint.centroid}  CRS: {footprint.epsg_string}")
```

---

## Querying bundles and groups

A `CameraBundle` is the top-level container (typically a survey campaign). It holds
one or more `CameraGroup` objects, each representing a single dive or deployment.

```python
from sealoc.models import Camera, CameraBundle, CameraGroup

with dal.session() as repos:
    # List all bundles and groups
    bundles: list[CameraBundle] = repos.bundles.get_all_by()
    groups: list[CameraGroup] = repos.groups.get_all_by()

    # Fetch a specific bundle by label
    bundle: CameraBundle | None = repos.bundles.get_one_by(label="survey_2023")

    if bundle is not None:
        # Flat list of all cameras across all groups in this bundle
        cameras: list[Camera] = bundle.cameras

        # Iterate over the groups within the bundle
        for group in bundle.groups:
            print(group.label, len(group.cameras))
```

You can also fetch a group directly and access only its cameras:

```python
with dal.session() as repos:
    group: CameraGroup | None = repos.groups.get_one_by(label="dive_01")

    if group is not None:
        cameras: list[Camera] = list(group.cameras)
```

---

## Accessing sensor, calibration, pose, and footprint

Each `Camera` links to a `CameraSensor` (which carries the `CameraCalibration`), and
optionally to a `CameraPose` and `CameraFootprint`. Use `has_pose()` and
`has_footprint()` to guard before calling `get_pose()` and `get_footprint()`.

```python
from sealoc.models import Camera, CameraCalibration, CameraFootprint, CameraPose, CameraSensor

camera: Camera = cameras[0]

sensor: CameraSensor = camera.sensor
calibration: CameraCalibration = sensor.calibration

# Intrinsics as a 3×3 numpy matrix and a distortion vector [k1, k2, p1, p2, k3]
K = calibration.intrinsic_matrix
d = calibration.distortion_vector

if camera.has_pose():
    pose: CameraPose = camera.get_pose()
    x, y, z = pose.location
    print(f"position: ({x:.2f}, {y:.2f}, {z:.2f})  CRS: {pose.epsg_string}")
    print(f"yaw={pose.yaw:.1f}  pitch={pose.pitch:.1f}  roll={pose.roll:.1f}")

if camera.has_footprint():
    footprint: CameraFootprint = camera.get_footprint()
    print(f"footprint vertices: {len(footprint.coordinates)}  CRS: {footprint.epsg_string}")
    print(f"centroid: {footprint.centroid}")
```

Collecting poses and footprints for all cameras in a group:

```python
with dal.session() as repos:
    group: CameraGroup = repos.groups.get_one_by(label="dive_01")

poses: list[CameraPose] = group.camera_poses
footprints: list[CameraFootprint] = group.camera_footprints
```

---

## Stereo rigs

Sensors and cameras support master/slave relationships for stereo rigs. The master is
the primary camera in the pair; slaves have their `master_camera` attribute set.

```python
with dal.session() as repos:
    group: CameraGroup | None = repos.groups.get_one_by(label="stereo_2023")

    if group is not None:
        master_cameras: list[Camera] = [
            camera for camera in group.cameras if camera.is_master
        ]
        slave_cameras: list[Camera] = [
            camera for camera in group.cameras if camera.is_slave
        ]

        for slave in slave_cameras:
            master: Camera | None = slave.master_camera
            if master is not None:
                print(f"slave {slave.label} → master {master.label}")
```

The same pattern applies to sensors:

```python
sensor: CameraSensor = camera.sensor

if sensor.is_master:
    print("this is the primary sensor in the rig")
else:
    master_sensor: CameraSensor | None = sensor.master_sensor
    print(f"slave sensor, master is: {master_sensor.label if master_sensor else 'unknown'}")
```

---

## Finding cameras with overlapping footprints

`CameraFootprintIndex` uses a Shapely STRtree over UTM-projected polygons to find
footprints that intersect a query footprint. A typical use case is cross-dive overlap:
build the index from a reference dive's footprints, then query with footprints from a
later dive to find the cameras that cover the same ground.

```python
from sealoc.geometry import (
    CameraFootprintIndex,
    CameraFootprintLink,
    create_camera_footprint_index,
)
from sealoc.models import Camera, CameraBundle, CameraFootprint, CameraGroup

with dal.session() as repos:
    bundle: CameraBundle = repos.bundles.get_one_by(label="survey_2023")
    database_group: CameraGroup = repos.groups.get_one_by(label="dive_01")
    query_group: CameraGroup = repos.groups.get_one_by(label="dive_02")

database_footprints: list[CameraFootprint] = database_group.camera_footprints
query_footprints: list[CameraFootprint] = query_group.camera_footprints

# Build the index once from the database group
index: CameraFootprintIndex = create_camera_footprint_index(database_footprints)

# Query with each footprint from the query group
for query_footprint in query_footprints:
    links: list[CameraFootprintLink] = index.search_links(query_footprint)
    for link in links:
        print(
            f"query camera {link.query_camera_id} ↔ "
            f"database camera {link.database_camera_id}: "
            f"IoU={link.footprint_iou:.3f}  "
            f"area={link.database_footprint_area:.1f} m²"
        )
```

You can also compute metrics on individual footprints using the geometry package:

```python
from sealoc.geometry import (
    calculate_footprint_area,
    calculate_footprint_iou,
)

area: float = calculate_footprint_area(query_footprints[0])
iou: float = calculate_footprint_iou(query_footprints[0], database_footprints[0])
```

---

## Finding cameras with spatially proximate poses

`CameraPoseIndex` finds all poses within a given distance (in meters) of a query pose.
Distances are computed in UTM space, auto-detected from the data. A typical use case is
cross-dive proximity: build the index from a reference dive's poses, then query with
poses from a later dive to find cameras that visited the same location.

```python
from sealoc.geometry import (
    CameraPoseIndex,
    CameraPoseLink,
    create_camera_pose_index,
)
from sealoc.models import Camera, CameraBundle, CameraGroup, CameraPose

with dal.session() as repos:
    bundle: CameraBundle = repos.bundles.get_one_by(label="survey_2023")
    database_group: CameraGroup = repos.groups.get_one_by(label="dive_01")
    query_group: CameraGroup = repos.groups.get_one_by(label="dive_02")

database_poses: list[CameraPose] = database_group.camera_poses
query_poses: list[CameraPose] = query_group.camera_poses

# Build the index once from the database group
index: CameraPoseIndex = create_camera_pose_index(database_poses)

# Query with each pose from the query group
for query_pose in query_poses:
    links: list[CameraPoseLink] = index.search_links(query_pose, max_distance=10.0)
    for link in links:
        print(
            f"query camera {link.query_camera_id} ↔ "
            f"database camera {link.database_camera_id}: "
            f"distance={link.distance_meters:.2f} m"
        )
```

You can also compute the distance between two poses directly:

```python
from sealoc.geometry import calculate_pose_distance

distance: float = calculate_pose_distance(query_poses[0], database_poses[0])
```

---

## Loading images

When `image_dir` is provided to `create_data_access_layer`, `dal.image_store` is an
`ImageStore` that maps `camera.image_label` to image files on disk. The image label
is the filename stem of the image (e.g. `"frame_0001"` for `frame_0001.jpg`).

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

`dal.image_store` is `None` when no image directory was given. `load_image` raises `KeyError`
if the label is not found in the store. Use `has_image` to guard first.

---

## Putting it all together

This example loads a bundle, separates two groups into a database group and a query
group, builds both spatial indices from the database group, then finds matching cameras
for every camera in the query group:

```python
from pathlib import Path

from sealoc.dal import create_data_access_layer, DataAccessLayer
from sealoc.geometry import (
    CameraFootprintIndex,
    CameraFootprintLink,
    CameraPoseIndex,
    CameraPoseLink,
    create_camera_footprint_index,
    create_camera_pose_index,
)
from sealoc.models import Camera, CameraBundle, CameraFootprint, CameraGroup, CameraPose

dal: DataAccessLayer = create_data_access_layer(
    database_url="sqlite:////data/sealoc/sealoc.db",
    image_dir=Path("/data/sealoc/sealoc_images_raw"),
)

with dal.session() as repos:
    bundle: CameraBundle = repos.bundles.get_one_by(label="survey_2023")
    database_group: CameraGroup = repos.groups.get_one_by(label="dive_01")
    query_group: CameraGroup = repos.groups.get_one_by(label="dive_02")

database_poses: list[CameraPose] = database_group.camera_poses
database_footprints: list[CameraFootprint] = database_group.camera_footprints

pose_index: CameraPoseIndex = create_camera_pose_index(database_poses)
footprint_index: CameraFootprintIndex = create_camera_footprint_index(database_footprints)

for query_camera in query_group.cameras:
    if query_camera.has_pose():
        pose_links: list[CameraPoseLink] = pose_index.search_links(
            query_camera.get_pose(), max_distance=15.0
        )

    if query_camera.has_footprint():
        footprint_links: list[CameraFootprintLink] = footprint_index.search_links(
            query_camera.get_footprint()
        )
```
