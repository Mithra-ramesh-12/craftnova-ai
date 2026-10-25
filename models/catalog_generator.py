import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if API_KEY and API_KEY not in (
    "YOUR_ACTUAL_GEMINI_API_KEY",
    "YOUR_GEMINI_API_KEY",
    "",
):
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as error:
        print("GEMINI CLIENT ERROR:", error)


MODEL_NAME = "gemini-3.5-flash-lite"

SUPPORTED_LANGUAGES = [
    "English",
    "Tamil",
    "Kannada",
    "Telugu",
    "Hindi",
    "Malayalam",
]


def generate_catalog(
    product_name,
    category,
    material,
    color,
    size,
    description,
    price,
    language="English",
):
    if language not in SUPPORTED_LANGUAGES:
        language = "English"

    if not product_name and not description:
        return (
            "Please provide a product name or description "
            "before generating the catalog."
        )

    if client is None:
        return (
            "Catalog generation is unavailable. "
            "Please check your Gemini API configuration."
        )

    product_details = (
        f"Product name: {product_name or 'Not provided'}\n"
        f"Category: {category or 'Not provided'}\n"
        f"Material: {material or 'Not provided'}\n"
        f"Color: {color or 'Not provided'}\n"
        f"Size: {size or 'Not provided'}\n"
        f"Description: {description or 'Not provided'}\n"
        f"Price: {price if price not in (None, '') else 'Not provided'}"
    )

    prompt = f"""
Create a concise, professional handmade-product catalog
entirely in {language}.

Use these supplied details:
{product_details}

Include:
1. Product name and category.
2. Product details that were provided.
3. A polished, short description.
4. The supplied price, if available.

Rules:
- Do not invent or change product facts.
- Preserve the supplied price and measurements.
- Do not add unsupported benefits or claims.
- Use simple headings and customer-friendly language.
- Keep the complete catalog under 150 words.
- Return plain text only.
"""

    print(f"CATALOG: Starting Gemini request ({language})...")
    start_time = time.perf_counter()

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=350,
                http_options=types.HttpOptions(
                    timeout=20000
                ),
            ),
        )

        elapsed = time.perf_counter() - start_time
        result = (response.text or "").strip()

        print(f"CATALOG: Gemini response time: {elapsed:.2f} seconds")

        if result:
            return result

        return "The catalog could not be generated. Please try again."

    except Exception as error:
        elapsed = time.perf_counter() - start_time

        print(f"CATALOG ERROR after {elapsed:.2f} seconds: {error}")

        return (
            "Catalog generation failed or timed out. "
            "Please try again. Check the VS Code terminal "
            "for the error details."
        )
