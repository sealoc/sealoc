"""
Immutable store for image sources and image loading.
"""

from collections.abc import (
    Iterable,
    Mapping,
)
from dataclasses import (
    dataclass,
    field,
)
from pathlib import Path

from sealoc.image import Image
from sealoc.image import read_image


VALID_IMAGE_SUFFIXES: tuple[str, ...] = (
    ".jpg",
    ".jpe",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
)


type ImageLabel = str
type ImageSource = str | Path


@dataclass(slots=True, frozen=True)
class ImageStore:
    """
    Immutable store mapping image labels to image sources.

    Attributes
    ----------
    image_sources: Mapping from image label to image source path.
    """

    image_sources: Mapping[ImageLabel, ImageSource] = field(default_factory=dict)

    @property
    def image_count(self) -> int:
        """
        Return the number of images in the store.

        Returns
        -------
        Number of images in the store.
        """
        return len(self.image_sources)

    @property
    def image_labels(self) -> Iterable[ImageLabel]:
        """
        Return the image labels in the store.

        Returns
        -------
        All image labels in the store.
        """
        return list(self.image_sources.keys())

    def has_image(self, label: ImageLabel) -> bool:
        """
        Return True if the label exists in the store.

        Arguments
        ---------
        label: Image label to check.

        Returns
        -------
        True if the label is present, False otherwise.
        """
        return label in self.image_sources

    def load_image(self, label: ImageLabel) -> Image:
        """
        Load the image for the given label.

        Arguments
        ---------
        label: Image label to load.

        Returns
        -------
        Loaded Image. Raises KeyError if the label is missing.
        """
        image_source: ImageSource | None = self.image_sources.get(label)
        if image_source is None:
            raise KeyError(f"missing image label: {label}")
        return read_image(image_source)


def create_image_store(
    *,
    image_dir: Path | str,
) -> ImageStore:
    """
    Create an image store from images in a directory tree.

    Arguments
    ---------
    image_dir: Root directory to scan for image files.

    Returns
    -------
    ImageStore populated with all image files found under image_dir.
    """
    image_sources: dict[ImageLabel, ImageSource] = _build_image_mapping_from_dir(
        image_dir
    )
    return ImageStore(image_sources)


def _build_image_mapping_from_dir(
    directory: Path | str,
) -> dict[ImageLabel, ImageSource]:
    """
    Build a label-to-source mapping from images in a directory tree.

    Arguments
    ---------
    directory: Root directory to scan recursively for image files.

    Returns
    -------
    Mapping from image stem (label) to absolute image path.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"path is not a directory: {directory}")

    all_files: list[Path] = [path for path in directory.rglob("*") if path.is_file()]
    image_files: list[Path] = [
        path for path in all_files if path.suffix.lower() in VALID_IMAGE_SUFFIXES
    ]

    return {path.stem: path for path in image_files}
