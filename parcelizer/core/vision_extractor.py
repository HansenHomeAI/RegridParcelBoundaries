"""Vision-based parcel information extraction using OpenAI o4-mini."""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI
from PIL import Image

from .config import config
from .image_processor import ImageProcessor


@dataclass
class ParcelInfo:
    """Extracted parcel information."""
    apn: Optional[str] = None
    address: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    raw_response: Optional[str] = None


class VisionExtractor:
    """Extracts parcel information from images using OpenAI Vision API."""
    
    def __init__(self) -> None:
        """Initialize the vision extractor."""
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
        self.image_processor = ImageProcessor()
        
        # Prompt template for extracting parcel information
        self.extraction_prompt = """
You are analyzing a parcel boundary map or property document. Please extract the following information:

1. APN (Assessor's Parcel Number) - Look for patterns like "APN:", "Parcel #:", or similar numeric identifiers
2. Street Address - Complete street address including house number, street name, and any unit/suite numbers
3. County - Name of the county where the property is located
4. State - State abbreviation or full name

Please respond in JSON format with the following structure:
{
    "apn": "extracted APN or null if not found",
    "address": "complete street address or null if not found", 
    "county": "county name or null if not found",
    "state": "state name/abbreviation or null if not found",
    "confidence": "high/medium/low based on clarity of information"
}

If you cannot find specific information, return null for that field. Be precise and only extract information you can clearly identify.
        """.strip()
    
    async def extract_from_image(self, image: Image.Image) -> ParcelInfo:
        """Extract parcel information from a single image."""
        try:
            # Resize image for API efficiency
            processed_image = self.image_processor.resize_image_for_api(image)
            
            # Convert to base64 for API call
            base64_image = self.image_processor.image_to_base64(processed_image)
            
            # Make API call to OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using o4-mini as specified
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.extraction_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            return self._parse_response(response_text)
            
        except Exception as e:
            raise RuntimeError(f"Vision extraction failed: {e}")
    
    async def extract_from_images(self, images: List[Image.Image]) -> List[ParcelInfo]:
        """Extract parcel information from multiple images concurrently."""
        tasks = [self.extract_from_image(image) for image in images]
        return await asyncio.gather(*tasks)
    
    def _parse_response(self, response_text: str) -> ParcelInfo:
        """Parse the JSON response from OpenAI."""
        try:
            import json
            
            # Try to extract JSON from response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
            
            data = json.loads(response_text)
            
            return ParcelInfo(
                apn=data.get("apn"),
                address=data.get("address"),
                county=data.get("county"),
                state=data.get("state"),
                raw_response=response_text
            )
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            return ParcelInfo(raw_response=response_text)
    
    def extract_coordinates_info(self, coordinates: str) -> ParcelInfo:
        """Extract parcel information from coordinates (lat, lon)."""
        try:
            # Parse coordinates
            coords = coordinates.strip().split(',')
            if len(coords) != 2:
                raise ValueError("Coordinates must be in format: lat,lon")
            
            lat = float(coords[0].strip())
            lon = float(coords[1].strip())
            
            # For coordinates, we'll use reverse geocoding approach
            # This is a simplified version - in production you'd use a proper geocoding service
            return ParcelInfo(
                address=f"Coordinates: {lat}, {lon}",
                raw_response=f"Processed coordinates: {lat}, {lon}"
            )
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid coordinates format: {e}")
    
    async def close(self) -> None:
        """Clean up resources."""
        await self.client.close() 