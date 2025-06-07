"""Flask web application for parcelizer."""

import asyncio
from pathlib import Path
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from ..core.config import config
from ..core.image_processor import ImageProcessor
from ..core.vision_extractor import VisionExtractor, ParcelInfo


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
            
            # Process the uploaded file
            images = image_processor.process_uploaded_file(file, file.filename)
            
            # Extract parcel information using vision API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                parcel_info_list = loop.run_until_complete(
                    vision_extractor.extract_from_images(images)
                )
            finally:
                loop.close()
            
            # Return results
            results = []
            for i, parcel_info in enumerate(parcel_info_list):
                results.append({
                    'image_index': i,
                    'apn': parcel_info.apn,
                    'address': parcel_info.address,
                    'county': parcel_info.county,
                    'state': parcel_info.state,
                    'raw_response': parcel_info.raw_response
                })
            
            return jsonify({
                'success': True,
                'results': results,
                'message': f'Processed {len(images)} image(s)'
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