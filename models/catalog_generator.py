import os

from dotenv import load_dotenv

load_dotenv()


try:

    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")

    if api_key and api_key != "YOUR_GEMINI_API_KEY":

        client = genai.Client(
            api_key=api_key
        )

    else:

        client = None

except Exception:

    client = None


def generate_catalog(
    product_name,
    category,
    material,
    color,
    size,
    description,
    price,
    language="English"
):

    prompt = f"""
Create a professional customer-facing smart catalog entry
for a handmade product.

IMPORTANT:
Write the complete catalog in {language}.
Do not mix languages unless the product name requires it.

Product Name:
{product_name}

Category:
{category}

Material:
{material}

Colour:
{color}

Size:
{size}

Original Details:
{description}

Price:
₹{price}

Create the following sections:

CATALOG TITLE
MARKETING DESCRIPTION
KEY FEATURES
PRODUCT SPECIFICATIONS
CRAFT STORY
IDEAL FOR
PRICE
CALL TO ACTION

Make the content attractive for customers.

Do not simply repeat the input fields.

Do not leave any section blank.
"""


    if client:

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            result = response.text

            if result and result.strip():

                return result.strip()

        except Exception:

            pass


    return f"""
CATALOG TITLE

{product_name} — Handcrafted {category}


MARKETING DESCRIPTION

Discover this beautifully handcrafted
{product_name}, created using {material}.


KEY FEATURES

• Handmade craftsmanship
• {material} construction
• {color} colour
• {size} size


PRODUCT SPECIFICATIONS

Product: {product_name}
Category: {category}
Material: {material}
Colour: {color}
Size: {size}


CRAFT STORY

This product represents the creativity
and craftsmanship behind handmade products.


IDEAL FOR

• Home decoration
• Gifting
• Personal collection
• Handmade product lovers


PRICE

₹{price}


CALL TO ACTION

Bring home this unique handmade creation today.
"""