from database.database import add_user, get_user


def register_user(name, email, password, language, craft_category, business_name):

    try:

        add_user(
            name,
            email,
            password,
            language,
            craft_category,
            business_name
        )

        return True

    except:

        return False


def login_user(email, password):

    return get_user(
        email,
        password
    )