from database.database import get_products
from models.catalog_generator import generate_catalog


def create_product_catalog(
    product_id,
    user_id,
    language="English"
):
    """
    Find a product belonging to the logged-in user
    and generate its catalog.
    """

    products = get_products(user_id)

    for product in products:

        # Existing product tuple:
        # 0 = ID
        # 1 = User ID
        # 2 = Product Name
        # 3 = Category
        # 4 = Material
        # 5 = Color
        # 6 = Size
        # 7 = Description
        # 8 = Price

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