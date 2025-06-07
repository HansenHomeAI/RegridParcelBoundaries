"""Configuration management for parcelizer."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """Configuration class for parcelizer."""

    def __init__(self) -> None:
        """Initialize configuration."""
        # Load environment variables from .env file
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.regrid_api_key = os.getenv("REGRID_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        if not self.regrid_api_key:
            raise ValueError("REGRID_API_KEY environment variable is required")
    
    @property
    def output_dir(self) -> Path:
        """Output directory for generated files."""
        return Path("output")
    
    def ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(exist_ok=True)


# Global configuration instance
config = Config() 