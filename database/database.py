import sqlite3
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "craftnova.db"
)


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            language TEXT DEFAULT 'English',
            craft_category TEXT,
            business_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            material TEXT,
            color TEXT,
            size TEXT,
            description TEXT,
            price REAL,
            original_image TEXT,
            enhanced_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            title TEXT,
            description TEXT,
            language TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    connection.commit()
    connection.close()


def add_user(
    name,
    email,
    password,
    language,
    craft_category,
    business_name
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users
        (
            name,
            email,
            password,
            language,
            craft_category,
            business_name
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        password,
        language,
        craft_category,
        business_name
    ))

    connection.commit()
    connection.close()


def get_user(email, password):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
        AND password = ?
    """, (
        email,
        password
    ))

    user = cursor.fetchone()

    connection.close()

    return user


def get_user_by_id(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    connection.close()

    return user


def update_user_language(
    user_id,
    language
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET language = ?
        WHERE id = ?
    """, (
        language,
        user_id
    ))

    connection.commit()

    connection.close()


def add_product(
    user_id,
    product_name,
    category,
    material,
    color,
    size,
    description,
    price,
    original_image,
    enhanced_image
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO products
        (
            user_id,
            product_name,
            category,
            material,
            color,
            size,
            description,
            price,
            original_image,
            enhanced_image
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        product_name,
        category,
        material,
        color,
        size,
        description,
        price,
        original_image,
        enhanced_image
    ))

    connection.commit()

    product_id = cursor.lastrowid

    connection.close()

    return product_id


def get_products(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    products = cursor.fetchall()

    connection.close()

    return products


def delete_product(
    product_id,
    user_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM products
        WHERE id = ?
        AND user_id = ?
    """, (
        product_id,
        user_id
    ))

    connection.commit()
    connection.close()


def add_catalog(
    product_id,
    title,
    description,
    language
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO catalogs
        (
            product_id,
            title,
            description,
            language
        )
        VALUES (?, ?, ?, ?)
    """, (
        product_id,
        title,
        description,
        language
    ))

    connection.commit()
    connection.close()


def initialize_database():

    create_tables()