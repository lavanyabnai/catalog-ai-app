from __future__ import annotations

import anthropic

from app.core.config import settings

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


_TOOL = {
    "name": "extract_garment_attributes",
    "description": "Extract structured product attributes from a garment image.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": (
                    "Short descriptive product name matching the style of fashion e-commerce listings. "
                    "Include color, print/pattern, fabric, and garment type. "
                    "Example: 'Mustard Cotton Hand Block Print Slim Fit Short Kurta'."
                ),
            },
            "color": {
                "type": "string",
                "description": "Primary color or color name. Example: 'Mustard', 'Sage Green', 'Navy Blue'.",
            },
            "material": {
                "type": "string",
                "description": "Primary fabric/material if discernible. Example: 'Cotton', 'Linen', 'Chiffon', 'Silk'.",
            },
            "category_hint": {
                "type": "string",
                "description": (
                    "Single garment category keyword. "
                    "Examples: 'kurta', 'dress', 'top', 'saree', 'lehenga', 'trouser', 'jacket', "
                    "'shirt', 'skirt', 'co-ord set', 'jumpsuit', 'blazer'."
                ),
            },
            "size_range": {
                "type": "string",
                "description": "Typical size range for this garment type. Example: 'XS, S, M, L, XL, XXL'.",
            },
        },
        "required": ["name", "color", "category_hint"],
    },
}


async def analyze_garment_image(image_b64: str, media_type: str = "image/jpeg") -> dict:
    client = _get_client()
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        tools=[_TOOL],  # type: ignore[list-item]
        tool_choice={"type": "tool", "name": "extract_garment_attributes"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,  # type: ignore[typeddict-item]
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analyze this garment image and extract product attributes "
                            "as they would appear in a fashion e-commerce listing."
                        ),
                    },
                ],
            }
        ],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_garment_attributes":
            return block.input  # type: ignore[return-value]
    return {}
