"""
Example script to load images from an image store.
"""

import click

from loguru import logger

from sealoc.dal.stores import (
    ImageStore,
    create_image_store,
)
from sealoc.image import Image


def test_image_store(image_directory: str) -> None:
    """
    Test an image store by creating it from a root directory.

    Arguments
    ---------
    image_directory: Path to the directory containing image files.
    """
    image_store: ImageStore = create_image_store(image_dir=image_directory)

    image_labels: list[str] = list(image_store.image_labels)
    logger.info("Image store:")
    logger.info(f" - Image count:   {image_store.image_count}")
    logger.info(f" - Image labels:  {len(image_labels)}")

    IMAGE_COUNT: int = 5
    for image_label in image_labels[:IMAGE_COUNT]:
        if not image_store.has_image(image_label):
            logger.warning(f"store does not contain image: {image_label}")
            continue

        image: Image | None = image_store.load_image(image_label)
        if image is None:
            logger.warning(f"error when loading image: {image_label}")
            continue

        logger.info(f" - Image format:          {image.pixel_format}")
        logger.info(f" - Image shape:           {image.shape}")
        logger.info(f" - Image layout:          {image.layout}")
        logger.info(f" - Image dtype:           {image.dtype}")
        logger.info(f" - Image numpy array:     {image.to_numpy().shape}")


@click.command()
@click.option(
    "--directory",
    "image_directory",
    type=click.Path(exists=True),
    required=True,
)
def main(image_directory: str) -> None:
    """Main function."""
    test_image_store(image_directory)


if __name__ == "__main__":
    main()
