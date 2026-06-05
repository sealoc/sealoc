# Data Model

## Overview

The SEALOC data model is a hierarchy of camera-related entities. At the top level, a
**CameraBundle** groups multiple **CameraGroup** objects, each of which contains a set
of **Camera** objects and their associated **CameraSensor** objects. Each camera may
optionally have a georeferenced **CameraPose** and a **CameraFootprint**.

```
CameraBundle
└── CameraGroup  (one or more)
    ├── CameraSensor  (one or more, with CameraCalibration)
    └── Camera  (one per captured image)
        ├── CameraPose        (optional — georeferenced position)
        └── CameraFootprint   (optional — ground coverage polygon)
```

## Entities

### CameraBundle

A `CameraBundle` is the top-level container. It typically represents a survey
campaign or expedition and groups all the dives or deployments that belong to it.

Key attributes:
- `id`, `label` — unique identifier and human-readable name
- `camera_groups` — the set of `CameraGroup` objects in this bundle
- `cameras` — flat list of all cameras across all groups (computed property)
- `camera_sensors` — flat list of all sensors across all groups (computed property)

### CameraGroup

A `CameraGroup` represents a single dive or deployment within a bundle. It holds the
cameras and sensors for that deployment.

Key attributes:
- `id`, `label` — unique identifier and human-readable name
- `cameras` — set of `Camera` objects in this group
- `camera_sensors` — set of `CameraSensor` objects in this group

### CameraSensor

A `CameraSensor` represents a physical imaging sensor. Multiple cameras (images) can
share the same sensor. Sensors support stereo rigs through master/slave relationships.

Key attributes:
- `id`, `label`
- `width`, `height` — image resolution in pixels
- `calibration` — the associated `CameraCalibration`
- `location`, `rotation` — sensor pose relative to a rig origin (Vec3 and Mat3)
- `is_master`, `is_slave` — whether this sensor is the primary in a stereo pair

### CameraCalibration

Intrinsic camera parameters and lens distortion coefficients.

Key attributes:
- `fx`, `fy` — focal lengths in pixels
- `cx`, `cy` — principal point (optical center)
- `k1`, `k2`, `k3` — radial distortion coefficients
- `p1`, `p2` — tangential distortion coefficients
- `intrinsic_matrix` — 3×3 numpy array (computed property)
- `distortion_vector` — `[k1, k2, p1, p2, k3]` numpy array (computed property)

### Camera

A `Camera` represents a single captured image. It links to the sensor that recorded
it and optionally to its georeferenced pose and footprint.

Key attributes:
- `id`, `label`
- `image_label` — key used to look up the image file in the `ImageStore`
- `sensor` — the associated `CameraSensor`
- `camera_pose` — georeferenced position, or `None`
- `camera_footprint` — ground coverage polygon, or `None`
- `is_master`, `is_slave` — stereo rig role
- `has_pose()`, `has_footprint()` — convenience checks

### CameraPose

A georeferenced camera position with orientation angles.

Key attributes:
- `camera_id` — links back to the `Camera`
- `location` — `(x, y, z)` coordinate tuple
- `srid` — EPSG code for the coordinate reference system
- `yaw`, `pitch`, `roll` — orientation angles in degrees
- `shape` — Shapely `Point` (computed property)
- `crs`, `epsg_string` — coordinate reference system helpers

### CameraFootprint

The projected ground coverage polygon for a camera image.

Key attributes:
- `camera_id` — links back to the `Camera`
- `coordinates` — list of `(x, y, z)` vertices
- `srid` — EPSG code
- `shape` — Shapely `Polygon` (computed property)
- `centroid` — centroid of the polygon (computed property)
- `crs`, `epsg_string` — coordinate reference system helpers

## Stereo rigs

Both `Camera` and `CameraSensor` support master/slave relationships for stereo rigs.
A master has `is_master=True` and `master_camera=None`. A slave has `is_slave=True`
and its `master_camera` pointing to the primary camera in the pair.

## Image loading

The `DataAccessLayer` optionally holds an `ImageStore`, which maps `image_label`
strings to file paths on disk. To load an image for a camera:

```python
from sealoc.dal import create_data_access_layer, DataAccessLayer
from sealoc.image import Image
from sealoc.models import Camera, CameraBundle

dal: DataAccessLayer = create_data_access_layer(image_dir="/data/sealoc/sealoc_images_raw")

with dal.session() as repos:
    bundle: CameraBundle | None = repos.bundles.get_one_by(label="survey_2023")
    for camera in bundle.cameras:
        if dal.image_store and dal.image_store.has_image(camera.image_label):
            image: Image = dal.image_store.load_image(camera.image_label)
```
