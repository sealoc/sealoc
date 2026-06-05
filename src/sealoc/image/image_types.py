"""
Core image types.

Defines the ImagePixelFormat enum, an ImageLayout value object, and an
Image wrapper around NumPy arrays with convenience accessors.
"""

import dataclasses
import enum
import typing

import numpy as np


class ImagePixelFormat(enum.StrEnum):
    """
    Pixel format of an image.

    Values encode the channel ordering and count, e.g. GRAY, RGB, or RGBA.
    """

    GRAY = enum.auto()
    X = enum.auto()
    RGB = enum.auto()
    BGR = enum.auto()
    XYZ = enum.auto()
    RGBA = enum.auto()
    BGRA = enum.auto()

    @property
    def channel_count(self) -> int:
        """
        Number of channels implied by this pixel format.

        Returns
        -------
        Channel count for this pixel format.
        """
        return _pixel_format_to_channel_count(self)


def _pixel_format_to_channel_count(pixel_format: ImagePixelFormat) -> int:
    """
    Map a pixel format to its number of channels.

    Intended for internal use by ImagePixelFormat.channel_count.

    Arguments
    ---------
    pixel_format: Pixel format to map.

    Returns
    -------
    Number of channels for the given pixel format.
    """
    match pixel_format:
        case ImagePixelFormat.GRAY:
            return 1
        case ImagePixelFormat.X:
            return 1
        case ImagePixelFormat.RGB:
            return 3
        case ImagePixelFormat.BGR:
            return 3
        case ImagePixelFormat.XYZ:
            return 3
        case ImagePixelFormat.RGBA:
            return 4
        case ImagePixelFormat.BGRA:
            return 4
        case _:
            raise NotImplementedError(f"invalid pixel format type: {pixel_format}")


@dataclasses.dataclass(frozen=True)
class ImageLayout:
    """
    Logical layout of an image: height, width, and channel count.

    Attributes
    ----------
    height: Image height in pixels.
    width: Image width in pixels.
    channels: Number of image channels.
    """

    height: int
    width: int
    channels: int

    @property
    def shape(self) -> tuple[int, int, int]:
        """
        Layout as a (height, width, channels) tuple.

        Returns
        -------
        Shape as a (height, width, channels) tuple.
        """
        return (self.height, self.width, self.channels)


# Create a generic variable that can be 'Parent', or any subclass.
T = typing.TypeVar("T", bound="Image")


@dataclasses.dataclass(frozen=True)
class Image:
    """
    Immutable image wrapper around a NumPy array.

    Exposes shape, layout, dtype, value range, and conversion helpers while
    tracking the pixel format.

    Attributes
    ----------
    _data: Underlying pixel data array of shape H×W×C.
    _pixel_format: Pixel format describing channel ordering and count.
    """

    _data: np.ndarray
    _pixel_format: ImagePixelFormat

    PixelFormat: typing.ClassVar[type[ImagePixelFormat]] = ImagePixelFormat
    Layout: typing.ClassVar[type[ImageLayout]] = ImageLayout

    @property
    def pixel_format(self) -> ImagePixelFormat:
        """
        Pixel format describing channel ordering and count.

        Returns
        -------
        Pixel format of the image.
        """
        return self._pixel_format

    @property
    def height(self) -> int:
        """
        Image height in pixels.

        Returns
        -------
        Height in pixels.
        """
        return self._data.shape[0]

    @property
    def width(self) -> int:
        """
        Image width in pixels.

        Returns
        -------
        Width in pixels.
        """
        return self._data.shape[1]

    @property
    def channels(self) -> int:
        """
        Number of channels in the image.

        Returns
        -------
        Number of channels.
        """
        return self._data.shape[2]

    @property
    def shape(self) -> tuple[int, int, int]:
        """
        Image shape as (height, width, channels).

        Returns
        -------
        Shape as a (height, width, channels) tuple.
        """
        return (self.height, self.width, self.channels)

    @property
    def layout(self) -> ImageLayout:
        """
        ImageLayout describing this image's dimensions and channels.

        Returns
        -------
        ImageLayout for this image.
        """
        return ImageLayout(*self._data.shape)

    @property
    def dtype(self) -> np.dtype:
        """
        NumPy dtype of the underlying pixel array.

        Returns
        -------
        dtype of the pixel array.
        """
        return self._data.dtype

    @property
    def ndim(self) -> int:
        """
        Number of dimensions of the underlying array.

        Returns
        -------
        Number of dimensions.
        """
        return self._data.ndim

    @property
    def min_value(self) -> int | float | bool:
        """
        Minimum pixel value in the image.

        Returns
        -------
        Minimum pixel value.
        """
        return np.min(self._data)

    @property
    def max_value(self) -> int | float | bool:
        """
        Maximum pixel value in the image.

        Returns
        -------
        Maximum pixel value.
        """
        return np.max(self._data)

    @classmethod
    def from_numpy(cls: type[T], data: np.ndarray, pixel_format: ImagePixelFormat) -> T:
        """
        Construct an Image from a NumPy array.

        Accepts 2D (H×W) or 3D (H×W×C) arrays and normalizes them to H×W×C.

        Arguments
        ---------
        data: Pixel array of shape H×W or H×W×C.
        pixel_format: Pixel format describing channel ordering and count.

        Returns
        -------
        Image with shape H×W×C.
        """
        if data.ndim == 2:
            data = np.expand_dims(data, axis=-1)
        elif data.ndim == 3:
            pass
        else:
            raise ValueError(f"invalid image data dimension: {data.ndim}")
        return cls(data, pixel_format)

    def to_numpy(self) -> np.ndarray:
        """
        Return a copy of the underlying pixel data as a NumPy array.

        Returns
        -------
        Copy of the pixel data array.
        """
        return self._data.copy()

    def copy(self) -> "Image":
        """
        Return a deep copy of the image object.

        Returns
        -------
        Deep copy of this Image.
        """
        return Image(self._data.copy(), self._pixel_format)
