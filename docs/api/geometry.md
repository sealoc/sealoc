# geometry

Spatial indices for finding cameras that are close to each other or that image
overlapping areas of the seafloor. Both indices are built on Shapely STRtrees and
project the data into an appropriate UTM CRS, detected automatically from the data,
so distances are in meters.

- [`CameraPoseIndex`][sealoc.geometry.CameraPoseIndex] finds poses within a distance
  of a query pose. Build it with
  [`create_camera_pose_index`][sealoc.geometry.create_camera_pose_index].
- [`CameraFootprintIndex`][sealoc.geometry.CameraFootprintIndex] finds footprints that
  intersect a query footprint. Build it with
  [`create_camera_footprint_index`][sealoc.geometry.create_camera_footprint_index].

```python
from sealoc.geometry import create_camera_footprint_index, create_camera_pose_index

pose_index = create_camera_pose_index(database_group.camera_poses)
footprint_index = create_camera_footprint_index(database_group.camera_footprints)

for query_camera in query_group.cameras:
    if query_camera.has_pose():
        pose_links = pose_index.search_links(query_camera.get_pose(), max_distance=15.0)
    if query_camera.has_footprint():
        footprint_links = footprint_index.search_links(query_camera.get_footprint())
```

`search` returns the matching poses or footprints. `search_links` returns
[`CameraPoseLink`][sealoc.geometry.CameraPoseLink] or
[`CameraFootprintLink`][sealoc.geometry.CameraFootprintLink] objects, which also carry
the distance or the footprint overlap between the query and each match.

!!! note "Same CRS"
    All poses or footprints used to build an index must share the same CRS. Query
    poses and footprints may use a different CRS; they are transformed into the
    index's CRS.

::: sealoc.geometry
