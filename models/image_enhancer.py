import os
import io
import threading

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw
from rembg import remove, new_session


# Load the background-removal model only when needed.
# This prevents Render from downloading the model at startup.
REMBG_SESSION = None
REMBG_LOCK = threading.Lock()


def get_rembg_session():
    global REMBG_SESSION

    if REMBG_SESSION is None:
        with REMBG_LOCK:
            if REMBG_SESSION is None:
                REMBG_SESSION = new_session("u2netp")

    return REMBG_SESSION


def remove_background(input_path):
    """Remove the original background and return a transparent RGBA image."""

    with open(input_path, "rb") as image_file:
        input_data = image_file.read()

    session = get_rembg_session()
    output_data = remove(input_data, session=session)

    image = Image.open(io.BytesIO(output_data)).convert("RGBA")
    return image


def crop_product(image):
    """Crop empty transparent space around the product."""

    alpha = image.getchannel("A")
    bbox = alpha.getbbox()

    if bbox:
        image = image.crop(bbox)

    return image


def create_background(size, style="auto"):
    """Create a professional product-photography background."""

    width, height = size

    backgrounds = {
        "white": (248, 248, 246),
        "warm": (238, 229, 214),
        "earthy": (226, 216, 199),
        "luxury": (232, 232, 228),
        "auto": (242, 239, 233),
    }

    base = np.array(
        backgrounds.get(style, backgrounds["auto"]),
        dtype=np.float32,
    )

    pixels = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        factor = 1.0 - (y / height) * 0.06
        pixels[y, :, :] = np.clip(base * factor, 0, 255).astype(
            np.uint8
        )

    return Image.fromarray(pixels)


def add_soft_shadow(background, product, position):
    """Add a subtle contact shadow beneath the product."""

    shadow_layer = Image.new(
        "RGBA",
        background.size,
        (0, 0, 0, 0),
    )

    product_width = product.width
    product_height = product.height

    shadow_width = max(1, int(product_width * 0.65))
    shadow_height = max(25, int(product_height * 0.035))

    shadow = Image.new(
        "RGBA",
        (shadow_width, shadow_height),
        (0, 0, 0, 0),
    )

    shadow_mask = Image.new(
        "L",
        (shadow_width, shadow_height),
        0,
    )

    draw = ImageDraw.Draw(shadow_mask)

    draw.ellipse(
        (0, 0, shadow_width - 1, shadow_height - 1),
        fill=95,
    )

    shadow_mask = shadow_mask.filter(
        ImageFilter.GaussianBlur(12)
    )

    shadow.putalpha(shadow_mask)

    x = position[0] + (product_width - shadow_width) // 2
    y = min(
        background.height - shadow_height,
        position[1] + product_height - 15,
    )
    y = max(0, y)

    shadow_layer.alpha_composite(shadow, (x, y))

    return Image.alpha_composite(
        background.convert("RGBA"),
        shadow_layer,
    )


def improve_product_image(image):
    """Improve lighting, contrast, colour, and sharpness."""

    image = ImageOps.exif_transpose(image)

    image = ImageEnhance.Brightness(image).enhance(1.04)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Color(image).enhance(1.04)
    image = ImageEnhance.Sharpness(image).enhance(1.20)

    return image


def enhance_image(
    input_path,
    output_path,
    background_style="auto",
):
    """Create a polished product image on a studio background."""

    if not os.path.exists(input_path):
        raise Exception("Input image was not found.")

    try:
        # STEP 1: Remove the original background.
        product = remove_background(input_path)

        # STEP 2: Crop empty transparent space.
        product = crop_product(product)

        # STEP 3: Improve the product image.
        product = improve_product_image(product)

        # STEP 4: Create the studio background.
        canvas_size = (1600, 1600)

        background = create_background(
            canvas_size,
            background_style,
        ).convert("RGBA")

        # STEP 5: Resize the product.
        product.thumbnail(
            (1250, 1250),
            Image.Resampling.LANCZOS,
        )

        # STEP 6: Centre the product.
        x = (canvas_size[0] - product.width) // 2
        y = (canvas_size[1] - product.height) // 2 - 30

        # Keep the product inside the canvas.
        y = max(0, min(y, canvas_size[1] - product.height))

        position = (x, y)

        # STEP 7: Add the soft shadow.
        background = add_soft_shadow(
            background,
            product,
            position,
        )

        # STEP 8: Place the product.
        background.alpha_composite(product, position)

        # STEP 9: Final image processing.
        final_image = background.convert("RGB")

        final_image = final_image.filter(
            ImageFilter.UnsharpMask(
                radius=1,
                percent=110,
                threshold=3,
            )
        )

        # STEP 10: Save the final image.
        output_directory = os.path.dirname(output_path)

        if output_directory:
            os.makedirs(output_directory, exist_ok=True)

        final_image.save(
            output_path,
            "JPEG",
            quality=95,
            optimize=True,
        )

        return output_path

    except Exception as e:
        raise Exception(f"Image enhancement failed: {str(e)}")