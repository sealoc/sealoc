# dal

The data access layer is the main entry point for reading SEALOC data. Create one with
[`load_data_access_layer`][sealoc.dal.load_data_access_layer], which reads
`SEALOC_DATABASE_URL` and `SEALOC_IMAGE_DIRECTORY` from the environment unless they are
passed explicitly.

```python
from sealoc.dal import load_data_access_layer

dal = load_data_access_layer()

with dal.session() as repositories:
    bundle = repositories.bundles.get_one_by(label="survey_2023")
    group = repositories.groups.get_one_by(label="dive_01")
```

All database queries happen inside [`dal.session()`][sealoc.dal.DataAccessLayer.session],
which yields a [`Repositories`][sealoc.dal.Repositories] object. The session commits on
success and rolls back on exception.

Poses and footprints are reached through the cameras themselves, with
[`Camera.get_pose`][sealoc.models.Camera.get_pose] and
[`Camera.get_footprint`][sealoc.models.Camera.get_footprint], or for a whole group with
[`CameraGroup.camera_poses`][sealoc.models.CameraGroup.camera_poses] and
[`CameraGroup.camera_footprints`][sealoc.models.CameraGroup.camera_footprints].

!!! note "Optional poses and footprints"
    Not every camera has a pose or a footprint. Check
    [`Camera.has_pose`][sealoc.models.Camera.has_pose] or
    [`Camera.has_footprint`][sealoc.models.Camera.has_footprint] before accessing them.

!!! tip "Images"
    `dal.image_store` is an [`ImageStore`][sealoc.dal.stores.ImageStore] when an image
    directory is configured, and `None` otherwise. Images are keyed by
    `camera.image_label`, the filename stem of the image (e.g. `"frame_0001"` for
    `frame_0001.jpg`). [`load_image`][sealoc.dal.stores.ImageStore.load_image] raises
    `KeyError` for unknown labels, so guard with
    [`has_image`][sealoc.dal.stores.ImageStore.has_image].

See the [Usage guide](../usage.md) for longer walkthroughs.

::: sealoc.dal

## Repositories

All repositories share the same query methods: `get_all_ids`, `get_by_id`, `get_one_by`
and `get_all_by`. The `get_one_by` and `get_all_by` methods take attribute filters as
keyword arguments, e.g. `get_one_by(label="dive_01")`.

::: sealoc.dal.repositories
    options:
      show_root_heading: false
      heading_level: 3

## Stores

::: sealoc.dal.stores
    options:
      show_root_heading: false
      heading_level: 3
