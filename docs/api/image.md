# image

A lightweight [`Image`][sealoc.image.Image] type with layout and pixel format metadata,
plus helpers for reading and writing image files. Images from the dataset are usually
loaded through the data access layer's image store; see
[`ImageStore.load_image`][sealoc.dal.stores.ImageStore.load_image].

```python
import torch

image = dal.image_store.load_image(camera.image_label)

image.layout        # ImageLayout(height=..., width=..., channels=...)
image.pixel_format  # ImagePixelFormat.RGB

array = image.to_numpy()
tensor = torch.from_numpy(array)
```

::: sealoc.image
