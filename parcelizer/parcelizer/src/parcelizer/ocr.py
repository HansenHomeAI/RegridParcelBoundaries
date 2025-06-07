"""OCR utilities using Tesseract."""
from __future__ import annotations

from pathlib import Path
from typing import List
from PIL import Image
import pytesseract


def load_images(path: Path) -> List[Image.Image]:
    """Load images from a file which may be PDF or an image."""
    if path.suffix.lower() == ".pdf":
        try:
            from pdf2image import convert_from_path
        except ImportError as exc:  # pragma: no cover - external
            raise RuntimeError("pdf2image required for PDF support") from exc
        return convert_from_path(str(path))
    return [Image.open(path)]


def extract_text(path: Path) -> str:
    """Run OCR on given file and return extracted text."""
    images = load_images(path)
    text_parts = [pytesseract.image_to_string(img) for img in images]
    return "\n".join(text_parts)
