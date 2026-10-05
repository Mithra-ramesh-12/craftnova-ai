import re


def clean_text(text):

    if not text:
        return ""

    return " ".join(text.strip().split())


def extract_product_details(text):

    text = clean_text(text)

    details = {
        "product_type": "",
        "material": "",
        "color": "",
        "size": "",
        "description": text
    }

    if not text:
        return details

    patterns = {

        "product_type":
        r"(?:product\s*(?:name)?|type)\s*(?:is|:|-)?\s*"
        r"(.+?)(?=\s+(?:made|material|color|colour|size|description)\b|$)",

        "material":
        r"(?:material|made\s+of|made\s+from)\s*(?:is|:|-)?\s*"
        r"(.+?)(?=\s+(?:color|colour|size|description|product|type)\b|$)",

        "color":
        r"(?:color|colour)\s*(?:is|:|-)?\s*"
        r"(.+?)(?=\s+(?:material|size|description|product|type)\b|$)",

        "size":
        r"(?:size)\s*(?:is|:|-)?\s*"
        r"(.+?)(?=\s+(?:material|color|colour|description|product|type)\b|$)"
    }

    for key, pattern in patterns.items():

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            details[key] = match.group(1).strip()

    return details