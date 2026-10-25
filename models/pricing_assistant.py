def suggest_price(
    product_type,
    material_cost,
    labour_cost,
    production_cost,
    market_info
):
    try:
        material_cost = float(material_cost)
        labour_cost = float(labour_cost)
        production_cost = float(production_cost)

        if min(material_cost, labour_cost, production_cost) < 0:
            return "Costs cannot be negative."

        total_cost = (
            material_cost
            + labour_cost
            + production_cost
        )

        if total_cost <= 0:
            return "Please enter a cost greater than zero."

        minimum = round(total_cost * 1.20, 2)
        recommended = round(total_cost * 1.35, 2)
        maximum = round(total_cost * 1.50, 2)

        market_info = (
            market_info.strip()
            if isinstance(market_info, str) and market_info.strip()
            else "No market information provided."
        )

        return f"""
AI PRICING RECOMMENDATION

Product:
{product_type}

Material Cost:
₹{material_cost:.2f}

Labour Cost:
₹{labour_cost:.2f}

Production Cost:
₹{production_cost:.2f}

Total Production Cost:
₹{total_cost:.2f}

Recommended Price:
₹{recommended:.2f}

Price Range:
₹{minimum:.2f} - ₹{maximum:.2f}

Reason:
The recommended price includes your material,
labour, and production costs with a 35% markup.

Market Consideration:
{market_info}

Important:
This is a cost-based estimate, not a verified
market price. Compare similar handmade products
before finalizing your selling price.
"""

    except (ValueError, TypeError) as error:
        print("PRICING ERROR:", error)
        return "Please enter valid numerical costs."