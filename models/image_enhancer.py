import io
import threading

REMBG_SESSION = None
REMBG_LOCK = threading.Lock()


def get_rembg_session():
    global REMBG_SESSION

    if REMBG_SESSION is None:
        with REMBG_LOCK:
            if REMBG_SESSION is None:
                print("Loading background-removal model...", flush=True)

                from rembg import new_session

                REMBG_SESSION = new_session("u2netp")

                print("Background-removal model loaded.", flush=True)

    return REMBG_SESSION


def remove_background(input_path):
    from PIL import Image
    from rembg import remove

    with open(input_path, "rb") as image_file:
        input_data = image_file.read()

    session = get_rembg_session()
    output_data = remove(input_data, session=session)

    image = Image.open(io.BytesIO(output_data)).convert("RGBA")

    return image


def crop_product(image):
    from PIL import Image

    if image.mode != "RGBA":
        image = image.convert("RGBA")

    alpha = image.getchannel("A")
    bbox = alpha.getbbox()

    if bbox:
        image = image.crop(bbox)

    return image


def create_background(size, color=(255, 255, 255, 255)):
    from PIL import Image

    return Image.new("RGBA", size, color)


def add_soft_shadow(image):
    from PIL import Image, ImageFilter

    image = image.convert("RGBA")

    alpha = image.getchannel("A")
    shadow_alpha = alpha.filter(ImageFilter.GaussianBlur(18))

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow.putalpha(shadow_alpha)

    return shadow


def improve_product_image(image):
    from PIL import Image, ImageEnhance, ImageOps

    image = ImageOps.exif_transpose(image)
    image = ImageEnhance.Color(image).enhance(1.08)
    image = ImageEnhance.Contrast(image).enhance(1.04)
    image = ImageEnhance.Sharpness(image).enhance(1.10)

    return image


def enhance_image(input_path, output_path=None, preset="professional"):
    """
    Enhance an artisan product image.

    Heavy image-processing libraries and the background-removal
    model are loaded only when this function is called.
    """

    from PIL import Image, ImageEnhance

    print("Starting product image enhancement...", flush=True)

    original = Image.open(input_path).convert("RGBA")
    original.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

    # Remove the background only when image enhancement is requested.
    product = remove_background(input_path)
    product.thumbnail((1250, 1250), Image.Resampling.LANCZOS)

    product = crop_product(product)
    product = improve_product_image(product)

    width, height = 1600, 1600

    backgrounds = {
        "clean_white": (255, 255, 255, 255),
        "warm_artisan": (248, 240, 225, 255),
        "natural_earthy": (237, 230, 214, 255),
        "premium_neutral": (242, 240, 235, 255),
        "professional": (255, 255, 255, 255),
        "auto": (255, 255, 255, 255),
    }

    background_color = backgrounds.get(
        preset,
        (255, 255, 255, 255)
    )

    background = create_background(
        (width, height),
        background_color
    )

    product.thumbnail((1250, 1250), Image.Resampling.LANCZOS)

    x = (width - product.width) // 2
    y = (height - product.height) // 2

    background.alpha_composite(product, (x, y))

    background = background.convert("RGB")
    background = ImageEnhance.Contrast(background).enhance(1.03)

    if output_path:
        background.save(
            output_path,
            "JPEG",
            quality=95,
            optimize=True
        )

        print("Enhanced image saved.", flush=True)
        return output_path

    output_buffer = io.BytesIO()

    background.save(
        output_buffer,
        format="JPEG",
        quality=95,
        optimize=True
    )

    output_buffer.seek(0)

    print("Image enhancement completed.", flush=True)

    return output_buffer