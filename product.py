import io

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage


def read_photo(photo_bytes):
    with Image.open(io.BytesIO(photo_bytes)) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def clean_mask(mask):
    mask = mask.convert("L").point(
        lambda value: 255 if value >= 250 else 0 if value <= 5 else value
    )
    values = np.array(mask)
    labels, count = ndimage.label(values > 0)
    if count == 0:
        raise ValueError("No product found. Try a clearer photograph.")
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    values[labels != sizes.argmax()] = 0
    return Image.fromarray(values)


def make_cutout(original, mask):
    box = mask.getbbox()
    if box is None:
        return None
    cutout = original.convert("RGBA")
    cutout.putalpha(mask)
    return cutout.crop(box)


def apply_brush(mask, x, y, radius, restore):
    edited = mask.copy()
    ImageDraw.Draw(edited).ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill=255 if restore else 0,
    )
    return edited
