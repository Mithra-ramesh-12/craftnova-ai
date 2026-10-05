import os
from database.database import add_product, get_products, delete_product

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "original")


def save_product(
    user_id,
    product_name,
    category,
    material,
    color,
    size,
    description,
    price,
    image
):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    image_path = ""

    if image:
        filename = image.filename
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(image_path)

    product_id = add_product(
        user_id,
        product_name,
        category,
        material,
        color,
        size,
        description,
        price,
        image_path,
        ""
    )

    return product_id


def get_user_products(user_id):
    return get_products(user_id)


def remove_product(product_id, user_id):
    delete_product(product_id, user_id)