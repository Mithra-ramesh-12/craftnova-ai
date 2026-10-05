from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_from_directory
)

from werkzeug.utils import secure_filename

import os


# ============================================================
# DATABASE
# ============================================================

from database.database import (
    initialize_database,
    add_user,
    get_user,
    get_user_by_id,
    add_product,
    get_products,
    delete_product,
    update_user_language
)


# ============================================================
# MODELS
# ============================================================

from models.language import translate
from models.translator import translate_text
from models.catalog_generator import generate_catalog
from models.image_enhancer import enhance_image
from models.pricing_assistant import suggest_price
from models.voice_input import extract_product_details


# ============================================================
# MODULES
# ============================================================

from modules.catalog_module import create_product_catalog
from modules.inventory_module import search_inventory


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "craftnova-secret-key-change-this"
)


# ============================================================
# BASE DIRECTORIES
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "original"
)


ENHANCED_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "enhanced"
)


# Create folders if they don't exist

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    ENHANCED_FOLDER,
    exist_ok=True
)


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["ENHANCED_FOLDER"] = ENHANCED_FOLDER

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# GLOBAL USER + LANGUAGE
# ============================================================

@app.context_processor
def inject_global_data():

    language = "English"

    current_user = None

    if "user_id" in session:

        current_user = get_user_by_id(
            session["user_id"]
        )

        if current_user:

            if current_user[4]:

                language = current_user[4]

    def t(text):

        return translate(
            text,
            language
        )

    return {
        "t": t,
        "current_language": language,
        "current_user": current_user
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        language = request.form.get(
            "language",
            "English"
        )

        craft_category = request.form.get(
            "craft_category",
            ""
        ).strip()

        business_name = request.form.get(
            "business_name",
            ""
        ).strip()


        # Required fields

        if not name or not email or not password:

            return render_template(
                "register.html",
                error="Please fill all required fields."
            )


        try:

            add_user(
                name,
                email,
                password,
                language,
                craft_category,
                business_name
            )

            return redirect(
                url_for("login")
            )


        except Exception:

            return render_template(
                "register.html",
                error="Email already exists or registration failed."
            )


    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        user = get_user(
            email,
            password
        )


        if user:

            session["user_id"] = user[0]

            session["user"] = user

            return redirect(
                url_for("dashboard")
            )


        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    user = get_user_by_id(
        session["user_id"]
    )


    if not user:

        session.clear()

        return redirect(
            url_for("login")
        )


    session["user"] = user


    products = get_products(
        session["user_id"]
    )


    return render_template(
        "dashboard.html",
        user=user,
        products=products,
        active_page="dashboard",
        page_title="Dashboard",
        page_subtitle="Overview of your CRAFTNOVA workspace"
    )


# ============================================================
# SETTINGS
# ============================================================

@app.route(
    "/settings",
    methods=["GET", "POST"]
)
def settings():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    user_id = session["user_id"]


    if request.method == "POST":

        language = request.form.get(
            "language",
            "English"
        )


        allowed_languages = [
            "English",
            "Tamil",
            "Kannada",
            "Telugu",
            "Hindi",
            "Malayalam"
        ]


        if language not in allowed_languages:

            language = "English"


        update_user_language(
            user_id,
            language
        )


        user = get_user_by_id(
            user_id
        )


        session["user"] = user


        return render_template(
            "settings.html",
            user=user,
            success=True,
            active_page="settings",
            page_title="Settings",
            page_subtitle="Manage your CRAFTNOVA preferences"
        )


    user = get_user_by_id(
        user_id
    )


    return render_template(
        "settings.html",
        user=user,
        active_page="settings",
        page_title="Settings",
        page_subtitle="Manage your CRAFTNOVA preferences"
    )


# ============================================================
# ADD PRODUCT
# ============================================================

@app.route(
    "/add-product",
    methods=["GET", "POST"]
)
def add_product_page():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        product_name = request.form.get(
            "product_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        material = request.form.get(
            "material",
            ""
        ).strip()

        color = request.form.get(
            "color",
            ""
        ).strip()

        size = request.form.get(
            "size",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        ).strip()


        image = request.files.get(
            "image"
        )


        original_image = ""


        if image and image.filename:

            filename = secure_filename(
                image.filename
            )


            original_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )


            image.save(
                original_path
            )


            original_image = filename


        add_product(
            session["user_id"],
            product_name,
            category,
            material,
            color,
            size,
            description,
            price,
            original_image,
            ""
        )


        return redirect(
            url_for("inventory")
        )


    return render_template(
        "add_product.html",
        active_page="add_product",
        page_title="Add Product",
        page_subtitle="Create a new handmade product"
    )


# ============================================================
# INVENTORY
# ============================================================

@app.route("/inventory")
def inventory():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    search = request.args.get(
        "search",
        ""
    )


    products = search_inventory(
        session["user_id"],
        search
    )


    return render_template(
        "inventory.html",
        products=products,
        search=search,
        active_page="inventory",
        page_title="Inventory",
        page_subtitle="Manage your handmade products"
    )


# ============================================================
# DELETE PRODUCT
# ============================================================

@app.route(
    "/delete-product/<int:product_id>"
)
def delete_product_route(
    product_id
):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    delete_product(
        product_id,
        session["user_id"]
    )


    return redirect(
        url_for("inventory")
    )


# ============================================================
# IMAGE ENHANCER
# ============================================================

@app.route(
    "/image-enhancer",
    methods=["GET", "POST"]
)
def image_enhancer():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        image = request.files.get(
            "image"
        )


        background_style = request.form.get(
            "background_style",
            "auto"
        )


        # ----------------------------------------------------
        # Check image
        # ----------------------------------------------------

        if not image or not image.filename:

            return render_template(
                "image_enhancer.html",
                error="Please select an image.",
                active_page="image_enhancer",
                page_title="Image Enhancer",
                page_subtitle="Create professional product photographs"
            )


        # ----------------------------------------------------
        # Secure filename
        # ----------------------------------------------------

        filename = secure_filename(
            image.filename
        )


        # ----------------------------------------------------
        # Original path
        # ----------------------------------------------------

        original_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )


        image.save(
            original_path
        )


        # ----------------------------------------------------
        # Enhanced filename
        # ----------------------------------------------------

        name, extension = os.path.splitext(
            filename
        )


        enhanced_filename = (
            "enhanced_"
            + name
            + ".jpg"
        )


        enhanced_path = os.path.join(
            app.config["ENHANCED_FOLDER"],
            enhanced_filename
        )


        # ----------------------------------------------------
        # Enhance image
        # ----------------------------------------------------

        try:

            enhance_image(
                original_path,
                enhanced_path,
                background_style
            )


            return render_template(
                "image_enhancer.html",
                original_image=filename,
                enhanced_image=enhanced_filename,
                active_page="image_enhancer",
                page_title="Image Enhancer",
                page_subtitle="Create professional product photographs"
            )


        except Exception as e:

            return render_template(
                "image_enhancer.html",
                error=str(e),
                active_page="image_enhancer",
                page_title="Image Enhancer",
                page_subtitle="Create professional product photographs"
            )


    return render_template(
        "image_enhancer.html",
        active_page="image_enhancer",
        page_title="Image Enhancer",
        page_subtitle="Create professional product photographs"
    )


# ============================================================
# SERVE UPLOADED / ENHANCED IMAGES
# ============================================================

@app.route(
    "/uploads/<path:filename>"
)
def uploaded_file(filename):

    if filename.startswith(
        "enhanced_"
    ):

        return send_from_directory(
            app.config["ENHANCED_FOLDER"],
            filename
        )


    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# ============================================================
# VOICE INPUT PAGE
# ============================================================

@app.route("/voice-input")
def voice_input():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "voice_input.html",
        active_page="voice_input",
        page_title="Voice Input",
        page_subtitle="Create product details using your voice"
    )


# ============================================================
# PROCESS VOICE
# ============================================================

@app.route(
    "/process-voice",
    methods=["POST"]
)
def process_voice():

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first."
        }), 401


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({
            "error": "No data received."
        }), 400


    text = data.get(
        "text",
        ""
    )


    if not text:

        return jsonify({
            "error": "No voice text received."
        }), 400


    try:

        details = extract_product_details(
            text
        )


        return jsonify(
            details
        )


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# TRANSLATE
# ============================================================

@app.route(
    "/translate",
    methods=["POST"]
)
def translate_route():

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first."
        }), 401


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({
            "error": "No data received."
        }), 400


    text = data.get(
        "text",
        ""
    )


    language = data.get(
        "language",
        "English"
    )


    if not text:

        return jsonify({
            "translated_text": ""
        })


    try:

        result = translate_text(
            text,
            language
        )


        return jsonify({
            "translated_text": result
        })


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# CATALOG
# ============================================================

@app.route("/catalog")
def catalog():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    products = get_products(
        session["user_id"]
    )


    return render_template(
        "catalog.html",
        products=products,
        active_page="catalog",
        page_title="AI Catalog",
        page_subtitle="Generate professional product catalogs"
    )


# ============================================================
# GENERATE CATALOG
# ============================================================

@app.route(
    "/generate-catalog/<int:product_id>"
)
def generate_catalog_route(
    product_id
):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    user = get_user_by_id(
        session["user_id"]
    )


    language = "English"


    if user and user[4]:

        language = user[4]


    try:

        catalog_text = create_product_catalog(
            product_id,
            session["user_id"],
            language
        )


        return render_template(
            "catalog_result.html",
            catalog_text=catalog_text,
            active_page="catalog",
            page_title="Catalog Result",
            page_subtitle="AI-generated product catalog"
        )


    except Exception as e:

        return render_template(
            "catalog_result.html",
            catalog_text=f"Catalog generation failed: {str(e)}",
            active_page="catalog",
            page_title="Catalog Result",
            page_subtitle="AI-generated product catalog"
        )


# ============================================================
# PRICING ASSISTANT
# ============================================================

@app.route(
    "/pricing",
    methods=["GET", "POST"]
)
def pricing():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    result = None


    if request.method == "POST":

        product_type = request.form.get(
            "product_type",
            ""
        ).strip()


        material_cost = request.form.get(
            "material_cost",
            "0"
        ).strip()


        labour_cost = request.form.get(
            "labour_cost",
            "0"
        ).strip()


        production_cost = request.form.get(
            "production_cost",
            "0"
        ).strip()


        market_info = request.form.get(
            "market_info",
            ""
        ).strip()


        try:

            result = suggest_price(
                product_type,
                material_cost,
                labour_cost,
                production_cost,
                market_info
            )


        except Exception as e:

            result = {
                "error": str(e)
            }


    return render_template(
        "pricing.html",
        result=result,
        active_page="pricing",
        page_title="Pricing Assistant",
        page_subtitle="Get smart pricing suggestions"
    )


# ============================================================
# MARKET
# ============================================================

@app.route("/market")
def market():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    products = get_products(
        session["user_id"]
    )


    return render_template(
        "market.html",
        products=products,
        active_page="market",
        page_title="Market",
        page_subtitle="Explore your product marketplace"
    )


# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    if "user_id" in session:

        return render_template(
            "base.html"
        ), 404

    return redirect(
        url_for("login")
    )


# ============================================================
# FILE TOO LARGE
# ============================================================

@app.errorhandler(413)
def file_too_large(error):

    return render_template(
        "image_enhancer.html",
        error="Image is too large. Please upload an image below 10 MB.",
        active_page="image_enhancer",
        page_title="Image Enhancer",
        page_subtitle="Create professional product photographs"
    ), 413


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )