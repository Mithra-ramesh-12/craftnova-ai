
import socket
import os

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
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# GEMINI CONNECTION FIX: PREFER IPV4
# ============================================================

# Some Windows networks have trouble connecting over IPv6.
# This workaround prefers IPv4 for the Gemini API hostname.
#
# It does not disable IPv6 for your computer or other websites.

_original_getaddrinfo = socket.getaddrinfo


def _prefer_ipv4_for_gemini(host, port, *args, **kwargs):

    results = _original_getaddrinfo(
        host,
        port,
        *args,
        **kwargs
    )

    hostname = host.decode() if isinstance(host, bytes) else host

    if (
        isinstance(hostname, str)
        and hostname.lower() == "generativelanguage.googleapis.com"
    ):

        ipv4_results = [
            result
            for result in results
            if result[0] == socket.AF_INET
        ]

        if ipv4_results:
            return ipv4_results

    return results


socket.getaddrinfo = _prefer_ipv4_for_gemini


# ============================================================
# DATABASE IMPORTS
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
# MODEL IMPORTS
# ============================================================

from models.language import translate
from models.translator import translate_text
from models.image_enhancer import enhance_image
from models.pricing_assistant import suggest_price
from models.voice_input import extract_product_details


# ============================================================
# MODULE IMPORTS
# ============================================================

from modules.catalog_module import create_product_catalog
from modules.inventory_module import search_inventory


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# SECRET KEY
# ============================================================

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


# ============================================================
# CREATE REQUIRED FOLDERS
# ============================================================

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENHANCED_FOLDER, exist_ok=True)


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
# GLOBAL USER / LANGUAGE CONTEXT
# ============================================================

@app.context_processor
def inject_global_data():

    current_user = None
    current_language = "English"

    if "user_id" in session:

        current_user = get_user_by_id(
            session["user_id"]
        )

        if current_user:
            current_language = current_user[4] or "English"

    def t(key):
        return translate(key, current_language)

    return {
        "t": t,
        "current_language": current_language,
        "current_user": current_user,
        "user": current_user
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

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

            return redirect(url_for("login"))

        except Exception as exc:

            print("REGISTRATION ERROR:", exc)

            return render_template(
                "register.html",
                error="Email already exists or registration failed."
            )

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        user = get_user(email, password)

        if user:

            session["user_id"] = user[0]
            session["user"] = user

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    products = get_products(user_id)

    return render_template(
        "dashboard.html",
        products=products,
        active_page="dashboard",
        page_title="Dashboard",
        page_subtitle="Manage your craft business with AI"
    )


# ============================================================
# SETTINGS
# ============================================================

@app.route("/settings", methods=["GET", "POST"])
def settings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":

        language = request.form.get(
            "language",
            "English"
        )

        update_user_language(user_id, language)

        updated_user = get_user_by_id(user_id)

        if updated_user:
            session["user"] = updated_user

        return redirect(url_for("settings"))

    return render_template(
        "settings.html",
        active_page="settings",
        page_title="Settings",
        page_subtitle="Manage your CRAFTNOVA preferences"
    )


# ============================================================
# ADD PRODUCT
# ============================================================

@app.route("/add-product", methods=["GET", "POST"])
def add_product_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        user_id = session["user_id"]

        product_name = request.form.get(
            "product_name", ""
        ).strip()

        category = request.form.get(
            "category", ""
        ).strip()

        material = request.form.get(
            "material", ""
        ).strip()

        color = request.form.get(
            "color", ""
        ).strip()

        size = request.form.get(
            "size", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        price = request.form.get(
            "price", "0"
        ).strip()

        image = request.files.get("image")
        image_filename = ""

        if image and image.filename:

            image_filename = secure_filename(
                image.filename
            )

            image_path = os.path.join(
                UPLOAD_FOLDER,
                image_filename
            )

            image.save(image_path)

        try:
            price_value = float(price)
        except (ValueError, TypeError):
            price_value = 0

        add_product(
            user_id,
            product_name,
            category,
            material,
            color,
            size,
            description,
            price_value,
            image_filename,
            ""
        )

        return redirect(url_for("inventory"))

    return render_template(
        "add_product.html",
        active_page="add_product",
        page_title="Add Product",
        page_subtitle="Add a new handmade product"
    )


# ============================================================
# INVENTORY
# ============================================================

@app.route("/inventory")
def inventory():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    search = request.args.get(
        "search", ""
    ).strip()

    products = search_inventory(
        user_id,
        search
    )

    return render_template(
        "inventory.html",
        products=products,
        search=search,
        active_page="inventory",
        page_title="Inventory",
        page_subtitle="Manage your products"
    )


# ============================================================
# DELETE PRODUCT
# ============================================================

@app.route("/delete-product/<int:product_id>")
def delete_product_route(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    delete_product(
        product_id,
        session["user_id"]
    )

    return redirect(url_for("inventory"))


# ============================================================
# IMAGE ENHANCER
# ============================================================

@app.route("/image-enhancer", methods=["GET", "POST"])
def image_enhancer():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        image = request.files.get("image")

        background_style = request.form.get(
            "background_style",
            "auto"
        )

        if not image or not image.filename:

            return render_template(
                "image_enhancer.html",
                error="Please select an image.",
                active_page="image_enhancer",
                page_title="Image Enhancer",
                page_subtitle="Create professional product photographs"
            )

        filename = secure_filename(image.filename)

        if not filename:

            return render_template(
                "image_enhancer.html",
                error="Please select a valid image filename.",
                active_page="image_enhancer",
                page_title="Image Enhancer",
                page_subtitle="Create professional product photographs"
            )

        original_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        image.save(original_path)

        name, extension = os.path.splitext(filename)

        enhanced_filename = "enhanced_" + name + ".jpg"

        enhanced_path = os.path.join(
            ENHANCED_FOLDER,
            enhanced_filename
        )

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

        except Exception as exc:

            print("IMAGE ENHANCER ERROR:", exc)

            return render_template(
                "image_enhancer.html",
                error="Image enhancement failed. Please try again.",
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
# UPLOADED FILES
# ============================================================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    if filename.startswith("enhanced_"):

        return send_from_directory(
            ENHANCED_FOLDER,
            filename
        )

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# ============================================================
# VOICE INPUT PAGE
# ============================================================

@app.route("/voice-input")
def voice_input():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "voice_input.html",
        active_page="voice_input",
        page_title="Voice Product Input",
        page_subtitle="Create products using your voice"
    )


# ============================================================
# PROCESS VOICE
# ============================================================

@app.route("/process-voice", methods=["POST"])
def process_voice():

    if "user_id" not in session:
        return redirect(url_for("login"))

    voice_text = request.form.get(
        "voice_text", ""
    ).strip()

    language = request.form.get(
        "language", "English"
    )

    if not voice_text:

        return render_template(
            "voice_input.html",
            error="Please speak or enter your product details.",
            confirmed=False,
            active_page="voice_input",
            page_title="Voice Product Input",
            page_subtitle="Create products using your voice"
        )

    product_details = extract_product_details(
        voice_text,
        language
    )

    if (
        not isinstance(product_details, dict)
        or product_details.get("error")
    ):

        error_message = (
            product_details.get(
                "error",
                "Could not process the voice input."
            )
            if isinstance(product_details, dict)
            else "Could not process the voice input. Please try again."
        )

        return render_template(
            "voice_input.html",
            error=error_message,
            voice_text=voice_text,
            confirmed=False,
            active_page="voice_input",
            page_title="Voice Product Input",
            page_subtitle="Create products using your voice"
        )

    session["voice_original_text"] = voice_text
    session["voice_english_text"] = ""
    session["voice_language"] = language
    session["voice_product_details"] = product_details

    return render_template(
        "voice_input.html",
        voice_text=voice_text,
        english_text="",
        product_details=product_details,
        confirmed=True,
        language=language,
        active_page="voice_input",
        page_title="Voice Product Input",
        page_subtitle="Review your professional product details"
    )


# ============================================================
# CONFIRM VOICE INPUT
# ============================================================

@app.route("/confirm-voice", methods=["POST"])
def confirm_voice():

    if "user_id" not in session:
        return redirect(url_for("login"))

    original_text = session.get(
        "voice_original_text", ""
    )

    language = session.get(
        "voice_language", "English"
    )

    saved_details = session.get(
        "voice_product_details", {}
    )

    if not original_text:
        return redirect(url_for("voice_input"))

    if (
        not isinstance(saved_details, dict)
        or saved_details.get("error")
    ):
        return redirect(url_for("voice_input"))

    product_name = request.form.get(
        "product_name",
        saved_details.get("product_name", "")
    ).strip()

    category = request.form.get(
        "category",
        saved_details.get("category", "")
    ).strip()

    material = request.form.get(
        "material",
        saved_details.get("material", "")
    ).strip()

    color = request.form.get(
        "color",
        saved_details.get("color", "")
    ).strip()

    size = request.form.get(
        "size",
        saved_details.get("size", "")
    ).strip()

    description = request.form.get(
        "description",
        saved_details.get("description", "")
    ).strip()

    price = request.form.get(
        "price",
        saved_details.get("price", "")
    ).strip()

    if not product_name and not description:

        return render_template(
            "voice_input.html",
            confirmed=True,
            voice_text=original_text,
            product_details={
                "product_name": product_name,
                "category": category,
                "material": material,
                "color": color,
                "size": size,
                "description": description,
                "price": price
            },
            language=language,
            error="Please provide a product name or description.",
            active_page="voice_input",
            page_title="Voice Product Input",
            page_subtitle="Review your professional product details"
        )

    from models.catalog_generator import generate_catalog

    catalog_text = generate_catalog(
        product_name=product_name,
        category=category,
        material=material,
        color=color,
        size=size,
        description=description,
        price=price,
        language=language
    )

    final_details = {
        "product_name": product_name,
        "category": category,
        "material": material,
        "color": color,
        "size": size,
        "description": description,
        "price": price
    }

    session["voice_product_details"] = final_details

    return render_template(
        "catalog_result.html",
        catalog_text=catalog_text,
        product_details=final_details,
        language=language,
        original_text=original_text,
        english_text="",
        active_page="voice_input",
        page_title="Generated Catalog",
        page_subtitle="Your professional product catalog"
    )


# ============================================================
# RE-ENTER VOICE
# ============================================================

@app.route("/rerecord-voice")
def rerecord_voice():

    if "user_id" not in session:
        return redirect(url_for("login"))

    session.pop("voice_original_text", None)
    session.pop("voice_english_text", None)
    session.pop("voice_language", None)
    session.pop("voice_product_details", None)

    return redirect(url_for("voice_input"))


# ============================================================
# TRANSLATE
# ============================================================

@app.route("/translate", methods=["POST"])
def translate_route():

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    text = data.get("text", "")

    target_language = data.get(
        "language", "English"
    )

    if not text:
        return jsonify({"translated": ""})

    try:

        translated = translate_text(
            text,
            target_language
        )

        return jsonify({
            "translated": translated
        })

    except Exception as exc:

        print("TRANSLATION ROUTE ERROR:", exc)

        return jsonify({
            "error": "Translation failed. Please try again."
        }), 500


# ============================================================
# CATALOG PAGE
# ============================================================

@app.route("/catalog")
def catalog():

    if "user_id" not in session:
        return redirect(url_for("login"))

    products = get_products(
        session["user_id"]
    )

    return render_template(
        "catalog.html",
        products=products,
        active_page="catalog",
        page_title="AI Catalog",
        page_subtitle="Generate professional catalogs"
    )


# ============================================================
# GENERATE CATALOG FROM PRODUCT
# ============================================================

@app.route("/generate-catalog/<int:product_id>")
def generate_catalog(product_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    user_data = get_user_by_id(user_id)

    language = (
        user_data[4]
        if user_data and user_data[4]
        else "English"
    )

    catalog_text = create_product_catalog(
        product_id,
        user_id,
        language
    )

    return render_template(
        "catalog_result.html",
        catalog_text=catalog_text,
        language=language,
        product_id=product_id,
        active_page="catalog",
        page_title="Generated Catalog",
        page_subtitle="Your AI-generated product catalog"
    )


# Backward-compatible endpoint used by existing templates.
app.add_url_rule(
    "/generate-catalog/<int:product_id>",
    endpoint="generate_catalog_route",
    view_func=generate_catalog
)


# ============================================================
# PRICING ASSISTANT
# ============================================================

@app.route("/pricing", methods=["GET", "POST"])
def pricing():

    if "user_id" not in session:
        return redirect(url_for("login"))

    result = None
    error = None

    if request.method == "POST":

        try:

            product_type = request.form.get(
                "product_type",
                "Handmade Product"
            ).strip() or "Handmade Product"

            material_raw = request.form.get(
                "material_cost", ""
            ).strip()

            labour_raw = request.form.get(
                "labour_cost", ""
            ).strip()

            production_raw = request.form.get(
                "production_cost", ""
            ).strip()

            market_info = request.form.get(
                "market_info", ""
            ).strip() or "No market information provided."

            if not material_raw or not labour_raw or not production_raw:

                raise ValueError(
                    "Please enter material, labour, and production costs."
                )

            material_cost = float(material_raw)
            labour_cost = float(labour_raw)
            production_cost = float(production_raw)

            if min(
                material_cost,
                labour_cost,
                production_cost
            ) < 0:

                raise ValueError(
                    "Costs cannot be negative."
                )

            if (
                material_cost
                + labour_cost
                + production_cost
            ) <= 0:

                raise ValueError(
                    "Enter at least one cost greater than zero."
                )

            result = suggest_price(
                product_type,
                material_cost,
                labour_cost,
                production_cost,
                market_info
            )

        except ValueError as exc:

            error = str(exc)

        except Exception as exc:

            print("SMART AI PRICING ERROR:", exc)

            error = (
                "Pricing could not be calculated. "
                "Please check the VS Code terminal."
            )

    return render_template(
        "pricing.html",
        result=result,
        error=error,
        active_page="pricing",
        page_title="AI Pricing Assistant",
        page_subtitle="Get smart pricing suggestions"
    )


# ============================================================
# MARKET
# ============================================================

@app.route("/market")
def market():

    if "user_id" not in session:
        return redirect(url_for("login"))

    products = get_products(
        session["user_id"]
    ) or []

    market_links = [
        {
            "name": "IndiaHandmade",
            "description": (
                "Explore a marketplace focused on Indian handmade products."
            ),
            "url": "https://www.indiahandmade.com/"
        },
        {
            "name": "ONDC",
            "description": (
                "Learn how sellers can participate through ONDC seller applications."
            ),
            "url": "https://ondc.org/"
        },
        {
            "name": "GeM",
            "description": (
                "Explore government procurement opportunities for eligible sellers."
            ),
            "url": "https://gem.gov.in/"
        }
    ]

    return render_template(
        "market.html",
        products=products,
        market_links=market_links,
        active_page="market",
        page_title="Market Linkage",
        page_subtitle="Prepare your products for wider market access"
    )


# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "dashboard.html",
        error="Page not found.",
        active_page="dashboard",
        page_title="Dashboard",
        page_subtitle="Manage your craft business with AI"
    ), 404


# ============================================================
# 413 ERROR - FILE TOO LARGE
# ============================================================

@app.errorhandler(413)
def file_too_large(error):

    return render_template(
        "image_enhancer.html",
        error="File is too large. Maximum allowed size is 10 MB.",
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
