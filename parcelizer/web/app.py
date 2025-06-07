"""Flask web application for parcelizer."""

import asyncio
import os
from pathlib import Path
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from ..core.config import config
from ..core.image_processor import ImageProcessor
from ..core.vision_extractor import VisionExtractor, ParcelInfo
from ..core.pipeline import ParcelPipeline


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.secret_key = "parcelizer-dev-key"  # In production, use a secure secret
    
    # Ensure output directory exists
    config.ensure_output_dir()
    
    # Initialize processors
    image_processor = ImageProcessor()
    vision_extractor = VisionExtractor()
    
    # Check for demo mode from environment or query parameter
    demo_mode = os.getenv('DEMO_MODE', 'false').lower() == 'true'
    pipeline = ParcelPipeline(demo_mode=demo_mode)
    
    @app.route('/')
    def index() -> str:
        """Render the main page."""
        return render_template('index.html')
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """Handle file upload and processing."""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not image_processor.is_supported_format(file.filename):
                return jsonify({'error': 'Unsupported file format'}), 400
            
            # Process the uploaded file through complete pipeline
            images = image_processor.process_uploaded_file(file, file.filename)
            
            # Process through pipeline (vision + regrid)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                parcel_results = loop.run_until_complete(
                    pipeline.process_images(images)
                )
            finally:
                loop.close()
            
            # Return results
            results = []
            map_data = pipeline.get_map_data(parcel_results)
            
            for i, result in enumerate(parcel_results):
                result_data = {
                    'image_index': i,
                    'apn': result.vision_info.apn,
                    'address': result.vision_info.address,
                    'county': result.vision_info.county,
                    'state': result.vision_info.state,
                    'success': result.success,
                    'error': result.error
                }
                
                # Add boundary info if available
                if result.boundary:
                    result_data.update({
                        'parcel_id': result.boundary.parcel_id,
                        'vertices_count': len(result.boundary.vertices) if result.boundary.vertices else 0,
                        'has_boundary': True
                    })
                else:
                    result_data['has_boundary'] = False
                
                results.append(result_data)
            
            return jsonify({
                'success': True,
                'results': results,
                'map_data': map_data,
                'message': f'Processed {len(images)} image(s) with {len([r for r in parcel_results if r.success])} successful boundary lookups'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/coordinates', methods=['POST'])
    def process_coordinates():
        """Handle coordinate input and processing."""
        try:
            data = request.get_json()
            coordinates = data.get('coordinates', '').strip()
            
            if not coordinates:
                return jsonify({'error': 'No coordinates provided'}), 400
            
            # Process coordinates
            parcel_info = vision_extractor.extract_coordinates_info(coordinates)
            
            result = {
                'apn': parcel_info.apn,
                'address': parcel_info.address,
                'county': parcel_info.county,
                'state': parcel_info.state,
                'raw_response': parcel_info.raw_response
            }
            
            return jsonify({
                'success': True,
                'result': result,
                'message': 'Coordinates processed successfully'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/static/<path:filename>')
    def static_files(filename: str):
        """Serve static files."""
        return send_from_directory('static', filename)
    
    @app.errorhandler(413)
    def too_large(e):
        """Handle file too large error."""
        return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413
    
    return app


def run_dev_server() -> None:
    """Run the development server."""
    app = create_app()
    app.run(host='127.0.0.1', port=8080, debug=True)


if __name__ == '__main__':
    run_dev_server() 