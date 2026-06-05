# API Reference

## DataAccessLayer

### `create_data_access_layer`

```python
from sealoc.dal import create_data_access_layer, DataAccessLayer

dal: DataAccessLayer = create_data_access_layer(
    database_url: str | None = None,
    image_dir: str | Path | None = None,
) -> DataAccessLayer
```

Factory function for creating a `DataAccessLayer`. Pass `database_url` and `image_dir`
explicitly. Both fall back to environment variables (`SEALOC_DB_URL`, `SEALOC_IMAGE_DIR`)
if not provided, but explicit arguments are recommended.

### `DataAccessLayer.session`

```python
with dal.session() as repos:
    ...
```

Context manager that opens a database session and yields a `Repositories` object.
Commits on success and rolls back on exception.

### `DataAccessLayer.image_store`

```python
dal.image_store  # ImageStore | None
```

Holds the `ImageStore` when an image directory was provided. `None` otherwise.

---

## Repositories

All repositories are accessed via `dal.session()`. Poses and footprints are accessed
through the `Camera` model itself via `camera.get_pose()` and `camera.get_footprint()`.

```python
with dal.session() as repos:
    repos.bundles    # CameraBundleRepository
    repos.groups     # CameraGroupRepository
```

### Shared methods

All repositories expose these methods (replace `<Entity>` with the relevant type):

#### `get_all_ids() -> set[int] | list[int]`

Returns all record IDs in the table.

```python
ids: set[int] = repos.bundles.get_all_ids()
```

#### `get_by_id(id: int) -> <Entity> | None`

Fetches a single record by its primary key. Returns `None` if not found.

```python
bundle: CameraBundle | None = repos.bundles.get_by_id(1)
```

#### `get_one_by(**filters) -> <Entity> | None`

Returns the first record matching the given field filters. Returns `None` if no match.

```python
bundle: CameraBundle | None = repos.bundles.get_one_by(label="survey_2023")
group: CameraGroup | None = repos.groups.get_one_by(label="dive_01")
```

#### `get_all_by(**filters) -> list[<Entity>]`

Returns all records matching the given field filters.

```python
groups: list[CameraGroup] = repos.groups.get_all_by(label="dive_01")
```

---

## Geometry indices

Geometry indices provide efficient spatial queries over poses and footprints using
Shapely STRtrees. They operate on UTM-projected coordinates derived automatically
from the data.

### `CameraPoseIndex`

```python
from sealoc.geometry import create_camera_pose_index, CameraPoseIndex

index: CameraPoseIndex = create_camera_pose_index(
    camera_poses: list[CameraPose],
) -> CameraPoseIndex
```

Builds a spatial index over a list of `CameraPose` objects. All poses must share
the same CRS.

#### `index.search(query_pose, max_distance) -> list[CameraPose]`

Returns all poses within `max_distance` meters of `query_pose`.

```python
neighbors: list[CameraPose] = index.search(query_pose=poses[0], max_distance=10.0)
```

### `CameraFootprintIndex`

```python
from sealoc.geometry import create_camera_footprint_index, CameraFootprintIndex

index: CameraFootprintIndex = create_camera_footprint_index(
    camera_footprints: list[CameraFootprint],
) -> CameraFootprintIndex
```

Builds a spatial index over a list of `CameraFootprint` objects. All footprints must
share the same CRS.

#### `index.search(query_footprint) -> list[CameraFootprint]`

Returns all footprints whose polygon intersects `query_footprint`.

```python
overlapping: list[CameraFootprint] = index.search(query_footprint=footprints[0])
```

---

## ImageStore

```python
dal.image_store.has_image(label: str) -> bool
dal.image_store.load_image(label: str) -> Image
dal.image_store.image_labels             # Iterable[str]
dal.image_store.image_count              # int
```

Maps image labels to files on disk. `Camera.image_label` is the filename stem of the
image (e.g. `"frame_0001"` for `frame_0001.jpg`) and is the correct key to use with
`has_image` and `load_image`. `load_image` raises `KeyError` if the label is missing.

The returned `Image` exposes layout and pixel format metadata, and can be converted
to NumPy or PyTorch:

```python
import numpy as np
import torch

image: Image = dal.image_store.load_image(camera.image_label)

print(image.layout)        # ImageLayout(height=..., width=..., channels=...)
print(image.pixel_format)  # ImagePixelFormat.RGB

array: np.ndarray = image.to_numpy()
tensor = torch.from_numpy(array)
```

---

## Full example

```python
from sealoc.dal import create_data_access_layer, DataAccessLayer
from sealoc.geometry import (
    CameraFootprintIndex,
    CameraPoseIndex,
    create_camera_footprint_index,
    create_camera_pose_index,
)
from sealoc.image import Image
from sealoc.models import Camera, CameraBundle, CameraFootprint, CameraPose

dal: DataAccessLayer = create_data_access_layer(
    database_url="sqlite:////data/sealoc/sealoc.db",
    image_dir="/data/sealoc/sealoc_images_raw",
)

with dal.session() as repos:
    bundle: CameraBundle | None = repos.bundles.get_one_by(label="survey_2023")
    cameras: list[Camera] = bundle.cameras
    poses: list[CameraPose] = [
        camera.get_pose() for camera in cameras if camera.has_pose()
    ]
    footprints: list[CameraFootprint] = [
        camera.get_footprint() for camera in cameras if camera.has_footprint()
    ]

pose_index: CameraPoseIndex = create_camera_pose_index(poses)
footprint_index: CameraFootprintIndex = create_camera_footprint_index(footprints)

nearby_poses: list[CameraPose] = pose_index.search(poses[0], max_distance=15.0)
overlapping: list[CameraFootprint] = footprint_index.search(footprints[0])

if dal.image_store:
    image: Image = dal.image_store.load_image(cameras[0].image_label)
```
