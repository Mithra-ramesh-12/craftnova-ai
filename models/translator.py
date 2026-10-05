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


def translate_text(text, target_language):

    if not text:
        return ""


    prompt = f"""
Translate the following text into {target_language}.

Important instructions:

- Preserve the original meaning.
- Do not add unnecessary information.
- Keep product names meaningful.
- Use natural language.
- Return only the translated text.

Text:

{text}
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


    return text