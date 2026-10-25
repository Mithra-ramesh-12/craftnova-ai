import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if API_KEY and API_KEY not in (
    "YOUR_ACTUAL_GEMINI_API_KEY",
    "YOUR_GEMINI_API_KEY",
    ""
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
    "Malayalam"
]


def get_language_code(language):
    language_codes = {
        "English": "en-IN",
        "Tamil": "ta-IN",
        "Kannada": "kn-IN",
        "Telugu": "te-IN",
        "Hindi": "hi-IN",
        "Malayalam": "ml-IN"
    }

    return language_codes.get(language, "en-IN")


def _clean_json_response(text):
    text = (text or "").strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def extract_product_details(voice_text, language="English"):

    if not voice_text or not voice_text.strip():
        return {
            "error": "Please speak or enter your product details."
        }

    if language not in SUPPORTED_LANGUAGES:
        language = "English"

    if client is None:
        return {
            "error": (
                "Gemini is unavailable. Check GEMINI_API_KEY "
                "in your .env file."
            )
        }

    fields = [
        "product_name",
        "category",
        "material",
        "color",
        "size",
        "description",
        "price"
    ]

    prompt = f"""
Extract product details from the artisan's speech.

Language: {language}

Speech:
{voice_text}

Return ONLY valid JSON using these exact keys:
{json.dumps(fields)}

Rules:
- Keep product_name and description in {language}.
- Correct grammar and make the description professional.
- Never invent missing product information.
- Use an empty string for information not supplied.
- Keep the supplied price unchanged.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        result = _clean_json_response(response.text)

        if not result:
            return {
                "error": "No response received. Please try again."
            }

        details = json.loads(result)

        return {
            field: str(details.get(field, "") or "").strip()
            for field in fields
        }

    except json.JSONDecodeError as error:
        print("VOICE JSON ERROR:", error)

        return {
            "error": (
                "The product details could not be processed. "
                "Please try speaking again."
            )
        }

    except Exception as error:
        print("VOICE PROCESSING ERROR:", error)

        return {
            "error": (
                "Voice processing failed. Check the VS Code "
                "terminal for the actual error."
            )
        }


def translate_product_details(product_details, target_language):

    if target_language not in SUPPORTED_LANGUAGES:
        target_language = "English"

    if not isinstance(product_details, dict):
        return {
            "error": "Invalid product details."
        }

    if client is None:
        return {
            "error": "Gemini is unavailable. Check your API key."
        }

    fields = [
        "product_name",
        "category",
        "material",
        "color",
        "size",
        "description",
        "price"
    ]

    prompt = f"""
Translate these product details into {target_language}.

Preserve the meaning, price, and measurements.
Do not add information.

Return ONLY valid JSON with these keys:
{json.dumps(fields)}

Product details:
{json.dumps(product_details, ensure_ascii=False)}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        result = _clean_json_response(response.text)
        translated = json.loads(result)

        return {
            field: str(translated.get(field, "") or "").strip()
            for field in fields
        }

    except Exception as error:
        print("TRANSLATION ERROR:", error)

        return {
            "error": "Translation failed. Please try again."
        }