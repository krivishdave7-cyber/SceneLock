import numpy as np
from PIL import Image
from scipy import ndimage


LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def _local_context(background, layer, box):
    """Sample visible background around the placed product, before shadows."""
    x0, y0, x1, y1 = box
    margin = max(16, min(96, round(max(x1 - x0, y1 - y0) * 0.2)))
    region = (
        max(0, x0 - margin), max(0, y0 - margin),
        min(background.width, x1 + margin), min(background.height, y1 + margin),
    )
    pixels = np.asarray(background.convert("RGBA").crop(region), dtype=np.float32)
    alpha = np.asarray(layer.getchannel("A").crop(region), dtype=np.uint8)
    footprint = ndimage.binary_dilation(alpha > 5, iterations=2)
    valid = (~footprint) & (pixels[..., 3] >= 250)
    if valid.sum() < 32:
        return None
    rgb = pixels[..., :3]
    grey = rgb @ LUMA
    # Ignore very dark objects and bright highlights in the surrounding surface.
    low, high = np.percentile(grey[valid], [15, 85])
    typical = valid & (grey >= low) & (grey <= high)
    if typical.sum() < 32:
        typical = valid
    return rgb, grey, typical


def _noise_level(grey, valid):
    """A rough grain estimate from low-gradient areas, not large scene edges."""
    if valid.sum() < 32:
        return 0.0
    smoothed = ndimage.gaussian_filter(grey.astype(np.float32), sigma=1.0)
    gradient = np.hypot(
        ndimage.sobel(smoothed, axis=0), ndimage.sobel(smoothed, axis=1),
    )
    threshold = np.percentile(gradient[valid], 55)
    flat = valid & (gradient <= threshold)
    if flat.sum() < 16:
        return 0.0
    residual = (grey - smoothed)[flat]
    return float(1.4826 * np.median(np.abs(residual - np.median(residual))))


def match_product_to_scene(background, product_layer, strength=45, softness=0.3, match_grain=True):
    """Conservative local colour/exposure matching; no generation or geometry changes.

    Alpha stays unchanged. At strength=0 this returns an exact copy, including RGB.
    Corrections are always calculated from the unmodified placed product.
    """
    if background.size != product_layer.size:
        raise ValueError("Background and product layer must have the same size.")
    amount = float(np.clip(strength, 0, 100)) / 100
    original = product_layer.convert("RGBA")
    box = original.getchannel("A").getbbox()
    if amount == 0 or box is None:
        return original.copy(), {"sampled": False, "grain": 0.0}
    context = _local_context(background, original, box)
    if context is None:
        return original.copy(), {"sampled": False, "grain": 0.0}

    patch = np.array(original.crop(box), dtype=np.uint8)
    rgb = patch[..., :3].astype(np.float32)
    alpha = patch[..., 3].astype(np.float32) / 255
    interior = ndimage.binary_erosion(alpha > 0.95, iterations=2)
    if interior.sum() < 16:
        interior = alpha > 0.5
    if not interior.any():
        return original.copy(), {"sampled": False, "grain": 0.0}
    bg_rgb, bg_grey, sample = context

    product_grey = rgb @ LUMA
    product_level = max(12.0, float(np.percentile(product_grey[interior], 65)))
    scene_level = max(12.0, float(np.percentile(bg_grey[sample], 65)))
    # A dark product should remain dark, even on a bright tabletop.
    exposure = float(np.clip((scene_level / product_level) ** 0.16, 0.86, 1.14))
    gain = 1 + amount * (exposure - 1)

    ambient = np.median(bg_rgb[sample], axis=0)
    # Only a small ambient cast, not wholesale foreground/background colour transfer.
    chroma = (ambient + 12) / (float(ambient.mean()) + 12)
    colour_gain = 1 + amount * np.clip((chroma - 1) * 0.15, -0.06, 0.06)
    adjusted = rgb * gain * colour_gain

    sigma = float(np.clip(softness, 0, 1.5))
    if sigma > 0:
        # Normalised premultiplied filtering avoids black transparent-edge halos.
        weight = ndimage.gaussian_filter(alpha, sigma=sigma)
        blurred = ndimage.gaussian_filter(
            adjusted * alpha[..., None], sigma=(sigma, sigma, 0),
        ) / np.maximum(weight[..., None], 1e-6)
        adjusted = np.where(
            alpha[..., None] > 0, adjusted * (1 - amount) + blurred * amount, adjusted,
        )

    grain = 0.0
    if match_grain:
        background_noise = _noise_level(bg_grey, sample)
        product_noise = _noise_level(product_grey, interior)
        grain = min(4.0, np.sqrt(max(0.0, background_noise**2 - product_noise**2))) * amount
        if grain > 0:
            # Stable noise: slider reruns do not cause a flickering random preview.
            rng = np.random.default_rng(12345)
            noise = rng.normal(0, grain, size=alpha.shape).astype(np.float32)
            adjusted += noise[..., None]

    visible = patch[..., 3] > 0
    converted = np.rint(np.clip(adjusted, 0, 255)).astype(np.uint8)
    patch[..., :3][visible] = converted[visible]
    matched = original.copy()
    matched.paste(Image.fromarray(patch), box[:2])
    return matched, {"sampled": True, "grain": float(grain)}
