"""Image processing utilities for parcel maps."""

import io
import base64
from pathlib import Path
from typing import List, Union, BinaryIO

from PIL import Image
import pytesseract

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


class ImageProcessor:
    """Handles image processing for parcel maps."""
    
    def __init__(self) -> None:
        """Initialize the image processor."""
        self.supported_formats = {".png", ".jpg", ".jpeg", ".pdf", ".tiff", ".bmp"}
    
    def is_supported_format(self, file_path: Union[str, Path]) -> bool:
        """Check if file format is supported."""
        return Path(file_path).suffix.lower() in self.supported_formats
    
    def process_uploaded_file(self, file: BinaryIO, filename: str) -> List[Image.Image]:
        """Process an uploaded file and return PIL Images."""
        file_path = Path(filename)
        file_extension = file_path.suffix.lower()
        
        if not self.is_supported_format(filename):
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        file_data = file.read()
        
        if file_extension == ".pdf":
            return self._process_pdf(file_data)
        else:
            return self._process_image(file_data)
    
    def _process_pdf(self, pdf_data: bytes) -> List[Image.Image]:
        """Process PDF file and extract images from each page."""
        if not PDF2IMAGE_AVAILABLE:
            raise NotImplementedError(
                "PDF processing requires pdf2image. Install with: pip install pdf2image"
            )
        
        try:
            # First try to open as image (some PDFs are just wrapped images)
            image = Image.open(io.BytesIO(pdf_data))
            return [image]
        except Exception:
            # Use pdf2image to convert PDF pages to images
            try:
                images = convert_from_bytes(pdf_data, dpi=200, fmt='PNG')
                return images
            except Exception as e:
                raise ValueError(f"Failed to process PDF: {e}")
    
    def _process_image(self, image_data: bytes) -> List[Image.Image]:
        """Process image file."""
        try:
            image = Image.open(io.BytesIO(image_data))
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            return [image]
        except Exception as e:
            raise ValueError(f"Failed to process image: {e}")
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string for API calls."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")
    
    def extract_text_with_ocr(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            return pytesseract.image_to_string(image)
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}")
    
    def save_image(self, image: Image.Image, output_path: Path) -> None:
        """Save image to file."""
        image.save(output_path)
    
    def resize_image_for_api(self, image: Image.Image, max_size: int = 1024) -> Image.Image:
        """Resize image to fit within max_size while maintaining aspect ratio."""
        if max(image.size) <= max_size:
            return image
        
        ratio = max_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        return image.resize(new_size, Image.Resampling.LANCZOS) 