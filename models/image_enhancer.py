import os
import cv2
import numpy as np

from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from rembg import remove, new_session


# Load the background removal model once
try:
    REMBG_SESSION = new_session("u2netp")
except Exception:
    REMBG_SESSION = None


def remove_background(input_path):
    """
    Removes the original background and returns
    a transparent RGBA image.
    """

    with open(input_path, "rb") as image_file:

        input_data = image_file.read()

    if REMBG_SESSION is not None:

        output_data = remove(
            input_data,
            session=REMBG_SESSION
        )

    else:

        output_data = remove(input_data)

    image = Image.open(
        __import__("io").BytesIO(output_data)
    ).convert("RGBA")

    return image


def crop_product(image):
    """
    Crops empty transparent space around the product.
    """

    alpha = image.getchannel("A")

    bbox = alpha.getbbox()

    if bbox:

        image = image.crop(bbox)

    return image


def create_background(size, style="auto"):
    """
    Creates a professional product photography background.
    """

    width, height = size

    if style == "white":

        background = Image.new(
            "RGB",
            size,
            (248, 248, 246)
        )

    elif style == "warm":

        background = Image.new(
            "RGB",
            size,
            (238, 229, 214)
        )

    elif style == "earthy":

        background = Image.new(
            "RGB",
            size,
            (226, 216, 199)
        )

    elif style == "luxury":

        background = Image.new(
            "RGB",
            size,
            (232, 232, 228)
        )

    else:

        # Auto professional studio background
        background = Image.new(
            "RGB",
            size,
            (242, 239, 233)
        )

    # Add a very subtle studio gradient
    pixels = np.zeros(
        (height, width, 3),
        dtype=np.uint8
    )

    base = np.array(
        background.resize((1, 1))
    )[0, 0]

    for y in range(height):

        factor = 1.0 - (y / height) * 0.06

        pixels[y, :, :] = np.clip(
            base * factor,
            0,
            255
        )

    return Image.fromarray(pixels)


def add_soft_shadow(background, product, position):
    """
    Adds a subtle realistic contact shadow.
    """

    shadow_layer = Image.new(
        "RGBA",
        background.size,
        (0, 0, 0, 0)
    )

    product_width = product.width
    product_height = product.height

    shadow_width = int(product_width * 0.65)
    shadow_height = max(
        25,
        int(product_height * 0.035)
    )

    shadow = Image.new(
        "RGBA",
        (
            shadow_width,
            shadow_height
        ),
        (0, 0, 0, 0)
    )

    shadow_mask = Image.new(
        "L",
        (
            shadow_width,
            shadow_height
        ),
        0
    )

    from PIL import ImageDraw

    draw = ImageDraw.Draw(shadow_mask)

    draw.ellipse(
        (
            0,
            0,
            shadow_width,
            shadow_height
        ),
        fill=95
    )

    shadow_mask = shadow_mask.filter(
        ImageFilter.GaussianBlur(12)
    )

    shadow.putalpha(shadow_mask)

    x = position[0] + (
        product_width - shadow_width
    ) // 2

    y = position[1] + product_height - 15

    shadow_layer.alpha_composite(
        shadow,
        (x, y)
    )

    return Image.alpha_composite(
        background.convert("RGBA"),
        shadow_layer
    )


def improve_product_image(image):
    """
    Improves lighting, contrast, color and sharpness
    without changing the actual product.
    """

    image = ImageOps.exif_transpose(image)

    # Slight lighting improvement
    image = ImageEnhance.Brightness(
        image
    ).enhance(1.04)

    # Improve contrast
    image = ImageEnhance.Contrast(
        image
    ).enhance(1.08)

    # Improve color
    image = ImageEnhance.Color(
        image
    ).enhance(1.04)

    # Improve sharpness
    image = ImageEnhance.Sharpness(
        image
    ).enhance(1.20)

    return image


def enhance_image(
    input_path,
    output_path,
    background_style="auto"
):

    if not os.path.exists(input_path):

        raise Exception(
            "Input image was not found."
        )

    try:

        # -------------------------------------------------
        # STEP 1: REMOVE ORIGINAL BACKGROUND
        # -------------------------------------------------

        product = remove_background(
            input_path
        )

        # -------------------------------------------------
        # STEP 2: CROP EMPTY AREA
        # -------------------------------------------------

        product = crop_product(product)

        # -------------------------------------------------
        # STEP 3: IMPROVE PRODUCT IMAGE
        # -------------------------------------------------

        product = improve_product_image(
            product
        )

        # -------------------------------------------------
        # STEP 4: CREATE PROFESSIONAL BACKGROUND
        # -------------------------------------------------

        canvas_size = (
            1600,
            1600
        )

        background = create_background(
            canvas_size,
            background_style
        )

        # -------------------------------------------------
        # STEP 5: RESIZE PRODUCT
        # -------------------------------------------------

        max_product_width = 1250
        max_product_height = 1250

        product.thumbnail(
            (
                max_product_width,
                max_product_height
            ),
            Image.Resampling.LANCZOS
        )

        # -------------------------------------------------
        # STEP 6: CENTER PRODUCT
        # -------------------------------------------------

        x = (
            canvas_size[0] - product.width
        ) // 2

        y = (
            canvas_size[1] - product.height
        ) // 2 - 30

        position = (
            x,
            y
        )

        # -------------------------------------------------
        # STEP 7: ADD SOFT SHADOW
        # -------------------------------------------------

        background = add_soft_shadow(
            background,
            product,
            position
        )

        # -------------------------------------------------
        # STEP 8: PLACE PRODUCT
        # -------------------------------------------------

        background.alpha_composite(
            product,
            position
        )

        # -------------------------------------------------
        # STEP 9: FINAL IMAGE
        # -------------------------------------------------

        final_image = background.convert(
            "RGB"
        )

        # Slight final sharpening
        final_image = final_image.filter(
            ImageFilter.UnsharpMask(
                radius=1,
                percent=110,
                threshold=3
            )
        )

        # -------------------------------------------------
        # STEP 10: SAVE
        # -------------------------------------------------

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True
        )

        final_image.save(
            output_path,
            "JPEG",
            quality=95,
            optimize=True
        )

        return output_path

    except Exception as e:

        raise Exception(
            f"Image enhancement failed: {str(e)}"
        )