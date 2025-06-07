"""Command-line interface for parcelizer."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from PIL import Image

from .core.config import config
from .core.image_processor import ImageProcessor
from .core.vision_extractor import VisionExtractor
from .web.app import run_dev_server


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Parcelizer: Local-first parcel boundary extraction tool."""
    pass


@cli.command()
@click.argument('image_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output directory (default: ./output)')
def process(image_path: Path, output: Optional[Path] = None):
    """Process a parcel map image and extract information."""
    if output is None:
        output = Path("output")
    
    output.mkdir(exist_ok=True)
    
    try:
        # Initialize processors
        image_processor = ImageProcessor()
        vision_extractor = VisionExtractor()
        
        # Check if file format is supported
        if not image_processor.is_supported_format(image_path):
            click.echo(f"Error: Unsupported file format: {image_path.suffix}")
            sys.exit(1)
        
        click.echo(f"Processing: {image_path}")
        
        # Process the image
        with open(image_path, 'rb') as f:
            images = image_processor.process_uploaded_file(f, image_path.name)
        
        click.echo(f"Extracted {len(images)} image(s)")
        
        # Extract parcel information
        click.echo("Extracting parcel information using OpenAI Vision...")
        
        async def extract_info():
            return await vision_extractor.extract_from_images(images)
        
        parcel_info_list = asyncio.run(extract_info())
        
        # Display results
        for i, parcel_info in enumerate(parcel_info_list):
            click.echo(f"\n--- Result {i + 1} ---")
            if parcel_info.apn:
                click.echo(f"APN: {parcel_info.apn}")
            if parcel_info.address:
                click.echo(f"Address: {parcel_info.address}")
            if parcel_info.county:
                click.echo(f"County: {parcel_info.county}")
            if parcel_info.state:
                click.echo(f"State: {parcel_info.state}")
            
            # Save raw response to file
            if parcel_info.raw_response:
                output_file = output / f"result_{i + 1}.json"
                with open(output_file, 'w') as f:
                    f.write(parcel_info.raw_response)
                click.echo(f"Raw response saved to: {output_file}")
        
        click.echo(f"\nProcessing complete! Results saved to: {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8080, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def serve(host: str, port: int, debug: bool):
    """Start the web server."""
    click.echo(f"Starting Parcelizer web server at http://{host}:{port}")
    
    from flask import Flask
    from .web.app import create_app
    
    app = create_app()
    app.run(host=host, port=port, debug=debug)


@cli.command()
@click.argument('coordinates', type=str)
def coords(coordinates: str):
    """Process coordinates and extract parcel information."""
    try:
        vision_extractor = VisionExtractor()
        parcel_info = vision_extractor.extract_coordinates_info(coordinates)
        
        click.echo(f"Coordinates: {coordinates}")
        if parcel_info.address:
            click.echo(f"Address: {parcel_info.address}")
        if parcel_info.raw_response:
            click.echo(f"Response: {parcel_info.raw_response}")
            
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main() 