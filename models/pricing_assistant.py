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


def suggest_price(
    product_type,
    material_cost,
    labour_cost,
    production_cost,
    market_info
):

    try:

        material_cost = float(material_cost)

    except:

        material_cost = 0


    try:

        labour_cost = float(labour_cost)

    except:

        labour_cost = 0


    try:

        production_cost = float(production_cost)

    except:

        production_cost = 0


    total_cost = (
        material_cost
        + labour_cost
        + production_cost
    )


    minimum = round(total_cost * 1.20)

    maximum = round(total_cost * 1.50)

    recommended = round(total_cost * 1.35)


    prompt = f"""

You are an AI pricing assistant for handmade products.

Product:
{product_type}

Material cost:
₹{material_cost}

Labour cost:
₹{labour_cost}

Production cost:
₹{production_cost}

Total cost:
₹{total_cost}

Market information:
{market_info}

Give a simple pricing recommendation.

Return:

Recommended Price:
Price Range:
Reason:
Market Consideration:

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

                return result

        except Exception:

            pass


    return f"""
Recommended Price:

₹{recommended}

Price Range:

₹{minimum} - ₹{maximum}

Reason:

The recommended price includes the material,
labour and production costs with a reasonable
margin for a handmade product.

Market Consideration:

Market information provided:
{market_info if market_info else "No market information provided."}

Total Basic Cost:

₹{total_cost}
"""