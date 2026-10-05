from database.database import get_products, delete_product


def search_inventory(user_id, search=""):

    products = get_products(user_id)

    if not search:

        return products


    search = search.lower().strip()

    result = []


    for product in products:

        product_name = str(product[2] or "").lower()

        category = str(product[3] or "").lower()

        material = str(product[4] or "").lower()

        color = str(product[5] or "").lower()


        if (
            search in product_name
            or search in category
            or search in material
            or search in color
        ):

            result.append(product)


    return result


def delete_inventory_product(product_id, user_id):

    delete_product(
        product_id,
        user_id
    )