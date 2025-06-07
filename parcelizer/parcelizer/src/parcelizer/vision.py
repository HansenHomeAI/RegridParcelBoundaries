"""Vision extraction via OpenAI."""
from __future__ import annotations

from pathlib import Path
import base64
import asyncio
import json

import openai


SYSTEM_PROMPT = "You extract parcel identifiers from maps."
USER_TEMPLATE = (
    "Given the following OCR text and image, extract JSON with keys 'parcel_id' "
    "and 'address', plus any county or state clues."
)


async def extract_metadata(image: Path, ocr_text: str) -> dict:
    """Extract parcel metadata from image and OCR text using OpenAI."""
    with image.open("rb") as fh:
        img_b64 = base64.b64encode(fh.read()).decode()
    client = openai.AsyncClient()
    response = await client.chat.completions.create(
        model="o4-mini-vision-latest",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_TEMPLATE + "\n" + ocr_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                ],
            },
        ],
        max_tokens=256,
    )
    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}
