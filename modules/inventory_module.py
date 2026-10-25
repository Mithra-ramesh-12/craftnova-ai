from database.database import get_products, delete_product


def search_inventory(user_id, search=""):
    """
    Return all products belonging to the user
    or filter products using a search term.
    """

    products = get_products(user_id)

    if not search or not search.strip():
        return products

    search = search.strip().casefold()

    matching_products = []

    for product in products:

        # Product tuple indexes from the existing project.
        product_name = str(product[2] or "").casefold()
        category = str(product[3] or "").casefold()
        material = str(product[4] or "").casefold()
        color = str(product[5] or "").casefold()

        if (
            search in product_name
            or search in category
            or search in material
            or search in color
        ):
            matching_products.append(product)

    return matching_products