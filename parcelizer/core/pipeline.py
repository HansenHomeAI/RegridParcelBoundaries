"""Integrated pipeline for parcel processing: Vision extraction + Regrid API."""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from PIL import Image

from .config import config
from .vision_extractor import VisionExtractor, ParcelInfo
from .regrid_client import RegridClient, ParcelBoundary
from .image_processor import ImageProcessor


@dataclass
class ParcelResult:
    """Complete parcel processing result."""
    vision_info: ParcelInfo
    boundary: Optional[ParcelBoundary] = None
    success: bool = False
    error: Optional[str] = None


class ParcelPipeline:
    """Complete pipeline for parcel processing."""
    
    def __init__(self, demo_mode: bool = False) -> None:
        """Initialize the pipeline."""
        self.vision_extractor = VisionExtractor()
        self.regrid_client = RegridClient(demo_mode=demo_mode)
        self.image_processor = ImageProcessor()
        self.demo_mode = demo_mode
        
        # Ensure output directory exists
        config.ensure_output_dir()
    
    async def process_images(self, images: List[Image.Image]) -> List[ParcelResult]:
        """Process images through the complete pipeline."""
        results = []
        
        # Step 1: Extract parcel information using vision
        print("Extracting parcel information using OpenAI Vision...")
        vision_results = await self.vision_extractor.extract_from_images(images)
        
        # Step 2: Look up each parcel in Regrid API
        print("Looking up parcel boundaries in Regrid API...")
        for i, vision_info in enumerate(vision_results):
            print(f"Processing result {i + 1}/{len(vision_results)}...")
            
            try:
                # Search for parcel boundary
                boundary = await self.regrid_client.search_parcel(
                    apn=vision_info.apn,
                    address=vision_info.address,
                    county=vision_info.county,
                    state=vision_info.state
                )
                
                if boundary:
                    # Save output files
                    parcel_id = boundary.apn or boundary.parcel_id or f"parcel_{i + 1}"
                    parcel_id = self._clean_filename(parcel_id)
                    
                    # Save GeoJSON
                    geojson_path = config.output_dir / f"{parcel_id}.geojson"
                    self.regrid_client.save_geojson(boundary, str(geojson_path))
                    
                    # Save vertices CSV
                    csv_path = config.output_dir / f"{parcel_id}_vertices.csv"
                    self.regrid_client.save_vertices_csv(boundary, str(csv_path))
                    
                    print(f"✓ Found parcel boundary for {parcel_id}")
                    print(f"  - Saved: {geojson_path.name}, {csv_path.name}")
                    
                    results.append(ParcelResult(
                        vision_info=vision_info,
                        boundary=boundary,
                        success=True
                    ))
                else:
                    print(f"✗ No boundary found for parcel {i + 1}")
                    results.append(ParcelResult(
                        vision_info=vision_info,
                        success=False,
                        error="No parcel boundary found in Regrid API"
                    ))
                    
            except Exception as e:
                print(f"✗ Error processing parcel {i + 1}: {e}")
                results.append(ParcelResult(
                    vision_info=vision_info,
                    success=False,
                    error=str(e)
                ))
        
        return results
    
    async def process_file(self, file_path: Path) -> List[ParcelResult]:
        """Process a file through the complete pipeline."""
        print(f"Processing file: {file_path}")
        
        # Process the file to extract images
        with open(file_path, 'rb') as f:
            images = self.image_processor.process_uploaded_file(f, file_path.name)
        
        print(f"Extracted {len(images)} image(s)")
        
        # Process through pipeline
        return await self.process_images(images)
    
    async def process_coordinates(self, coordinates: str) -> ParcelResult:
        """Process coordinates through the pipeline."""
        # For coordinates, we skip vision extraction and go straight to reverse geocoding
        # This is a simplified approach - in production you'd use a proper geocoding service
        vision_info = self.vision_extractor.extract_coordinates_info(coordinates)
        
        return ParcelResult(
            vision_info=vision_info,
            success=True,
            error="Coordinate processing not yet integrated with Regrid API"
        )
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename for safe file saving."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
    
    def get_map_data(self, results: List[ParcelResult]) -> Dict[str, Any]:
        """Get map data for visualization."""
        features = []
        bounds = []
        
        for result in results:
            if result.success and result.boundary and result.boundary.geometry:
                # Add feature for map
                feature = {
                    "type": "Feature",
                    "geometry": result.boundary.geometry,
                    "properties": {
                        "parcel_id": result.boundary.parcel_id,
                        "apn": result.boundary.apn,
                        "address": result.boundary.address,
                        "county": result.boundary.county,
                        "state": result.boundary.state
                    }
                }
                features.append(feature)
                
                # Calculate bounds for map centering
                if result.boundary.vertices:
                    for lat, lon in result.boundary.vertices:
                        bounds.append([lat, lon])
        
        # Calculate map center and zoom
        center = None
        if bounds:
            min_lat = min(point[0] for point in bounds)
            max_lat = max(point[0] for point in bounds)
            min_lon = min(point[1] for point in bounds)
            max_lon = max(point[1] for point in bounds)
            
            center = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "center": center,
            "bounds": bounds
        }
    
    async def close(self) -> None:
        """Clean up resources."""
        await self.vision_extractor.close() 