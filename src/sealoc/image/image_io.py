"""
Image I/O helpers built on top of imageio.

Provides functions to read images into the Image type and to write
Image or NumPy arrays back to disk or other URIs.
"""

import imageio.v3 as iio
import numpy as np

from pathlib import Path

from .image_types import (
    Image,
    ImagePixelFormat,
)


def _infer_pixel_format(values: np.ndarray) -> ImagePixelFormat:
    """
    Infer an ImagePixelFormat from the array dtype and channel count.

    Distinguishes between grayscale vs. color and floating-point vs. integer data.

    Arguments
    ---------
    values: NumPy array of shape H×W×C.

    Returns
    -------
    Inferred ImagePixelFormat for the array.
    """
    dtype: np.dtype = values.dtype
    channels: int = values.shape[2]

    is_floating_point: bool = dtype in [np.float16, np.float32, np.float64]

    match channels:
        case 1:
            return Image.PixelFormat.X if is_floating_point else Image.PixelFormat.GRAY
        case 3:
            return Image.PixelFormat.XYZ if is_floating_point else Image.PixelFormat.RGB
        case 4:
            return Image.PixelFormat.RGBA
        case _:
            raise ValueError(
                f"invalid combination of dtype and channels: {dtype}, {values}"
            )


def read_image(
    uri: str | Path,
    *,
    index: int | None = None,
    plugin: str | None = None,
    extension: str | None = None,
    **kwargs,
) -> Image:
    """
    Read an image from a URI into an Image.

    Uses imageio.v3.imread under the hood and returns an Image with shape H×W×C.
    Additional keyword arguments are passed through to imageio.

    Arguments
    ---------
    uri: File path or URI to read the image from.
    index: Frame index for multi-frame images.
    plugin: imageio plugin to use.
    extension: File extension hint for format detection.

    Returns
    -------
    Image with shape H×W×C.
    """
    try:
        read_kwargs: dict = {}
        if index is not None:
            read_kwargs["index"] = index
        if plugin is not None:
            read_kwargs["plugin"] = plugin
        if extension is not None:
            read_kwargs["extension"] = extension
        values: np.ndarray = iio.imread(uri, **read_kwargs, **kwargs)

        if values.ndim != 3:
            values = np.expand_dims(values, axis=2)

        _metadata: dict = iio.immeta(uri)
        pixel_format: ImagePixelFormat = _infer_pixel_format(values)
        return Image.from_numpy(data=values, pixel_format=pixel_format)
    except (OSError, IOError, TypeError, ValueError) as error:
        raise error


def write_image(
    image: Image | np.ndarray,
    uri: str | Path,
    *,
    plugin: str | None = None,
    extension: str | None = None,
    **kwargs,
) -> Path | str:
    """
    Write an image to a URI using imageio.

    Accepts either an Image instance or a raw NumPy array. Returns the URI on
    success; forwards extra keyword arguments to imageio.v3.imwrite.

    Arguments
    ---------
    image: Image or NumPy array to write.
    uri: Destination file path or URI.
    plugin: imageio plugin to use.
    extension: File extension hint for format detection.

    Returns
    -------
    The URI on success.
    """
    if isinstance(image, Image):
        values: np.ndarray = image.to_numpy()
    elif isinstance(image, np.ndarray):
        values = image
    else:
        return f"invalid image type: {type(image)}"

    try:
        iio.imwrite(uri, np.squeeze(values), **kwargs)
        return uri
    except (OSError, IOError, TypeError, ValueError) as error:
        raise error
