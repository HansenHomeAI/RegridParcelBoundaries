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
from .core.pipeline import ParcelPipeline
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
@click.option('--demo', is_flag=True, help='Use demo mode with sample parcel data')
def process(image_path: Path, output: Optional[Path] = None, demo: bool = False):
    """Process a parcel map image and extract information."""
    if output is None:
        output = Path("output")
    
    output.mkdir(exist_ok=True)
    
    try:
        # Initialize pipeline
        pipeline = ParcelPipeline(demo_mode=demo)
        
        if demo:
            click.echo("🎭 Running in demo mode with sample parcel data")
        
        # Check if file format is supported
        if not pipeline.image_processor.is_supported_format(image_path):
            click.echo(f"Error: Unsupported file format: {image_path.suffix}")
            sys.exit(1)
        
        click.echo(f"Processing: {image_path}")
        
        # Process through complete pipeline
        async def process_file():
            return await pipeline.process_file(image_path)
        
        results = asyncio.run(process_file())
        
        # Display results
        successful_parcels = 0
        for i, result in enumerate(results):
            click.echo(f"\n--- Result {i + 1} ---")
            
            # Vision extraction results
            if result.vision_info.apn:
                click.echo(f"APN: {result.vision_info.apn}")
            if result.vision_info.address:
                click.echo(f"Address: {result.vision_info.address}")
            if result.vision_info.county:
                click.echo(f"County: {result.vision_info.county}")
            if result.vision_info.state:
                click.echo(f"State: {result.vision_info.state}")
            
            # Boundary lookup results
            if result.success and result.boundary:
                successful_parcels += 1
                click.echo(f"✓ Parcel Boundary: Found ({len(result.boundary.vertices)} vertices)")
                click.echo(f"  Parcel ID: {result.boundary.parcel_id}")
                
                # Files should already be saved by pipeline
                parcel_id = pipeline._clean_filename(result.boundary.parcel_id)
                click.echo(f"  Files saved: {parcel_id}.geojson, {parcel_id}_vertices.csv")
            else:
                click.echo(f"✗ Parcel Boundary: Not found")
                if result.error:
                    click.echo(f"  Error: {result.error}")
        
        click.echo(f"\nProcessing complete!")
        click.echo(f"- Processed {len(results)} parcel(s)")
        click.echo(f"- Found boundaries for {successful_parcels} parcel(s)")
        click.echo(f"- Results saved to: {output}")
        
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