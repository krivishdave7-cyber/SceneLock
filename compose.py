from PIL import Image, ImageChops, ImageFilter


def compose_scene(background, product_layer, shadow_strength, shadow_direction="Under product"):
    scene = background.copy()
    alpha = product_layer.getchannel("A")
    box = alpha.getbbox()
    if shadow_strength > 0 and box is not None:
        unit = max(1, min(box[2] - box[0], box[3] - box[1]))
        amount = min(70, max(0, shadow_strength)) / 100
        # Tight contact plus a softer cast shadow, scaled to the product itself.
        contact = alpha.filter(ImageFilter.GaussianBlur(max(0.5, min(2.5, unit * 0.01))))
        contact = contact.point(lambda value: round(value * amount * 0.65))
        directions = {
            "Under product": (0, 0), "Down-right": (1, 1),
            "Down-left": (-1, 1), "Up-right": (1, -1), "Up-left": (-1, -1),
        }
        dx, dy = directions.get(shadow_direction, (0, 0))
        offset = max(1, round(unit * 0.025))
        cast = Image.new("L", background.size, 0)
        cast.paste(alpha, (dx * offset, dy * offset))
        cast = cast.filter(ImageFilter.GaussianBlur(max(1.5, min(12, unit * 0.045))))
        cast = cast.point(lambda value: round(value * amount * 0.75))
        mask = ImageChops.lighter(contact, cast)
        shadow = Image.new("RGBA", background.size, (0, 0, 0, 0))
        shadow.putalpha(mask)
        scene = Image.alpha_composite(scene, shadow)
    return Image.alpha_composite(scene, product_layer)


def place_product(background, cutout, size, angle, horizontal, vertical):
    width, height = background.size
    fit = min(width * 0.9 / cutout.width, height * 0.9 / cutout.height)
    scale = fit * size / 100
    adjusted = cutout.resize(
        (max(1, round(cutout.width * scale)), max(1, round(cutout.height * scale))),
        Image.Resampling.LANCZOS,
    ).rotate(
        angle, resample=Image.Resampling.BICUBIC, expand=True,
        fillcolor=(0, 0, 0, 0),
    )
    x = round(width / 2 + horizontal * width / 200 - adjusted.width / 2)
    y = round(height / 2 + vertical * height / 200 - adjusted.height / 2)
    layer = Image.new("RGBA", background.size, (0, 0, 0, 0))
    layer.paste(adjusted, (x, y))
    clipped = x < 0 or y < 0 or x + adjusted.width > width or y + adjusted.height > height
    return layer, clipped
