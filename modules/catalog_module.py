from models.catalog_generator import generate_catalog
from database.database import get_products


def create_product_catalog(
    product_id,
    user_id,
    language="English"
):

    products = get_products(user_id)

    for product in products:

        if product[0] == product_id:

            return generate_catalog(
                product[2],
                product[3],
                product[4],
                product[5],
                product[6],
                product[7],
                product[8],
                language
            )

    return "Product not found."