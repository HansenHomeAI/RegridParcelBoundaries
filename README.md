# Parcelizer

Local-first parcel boundary extraction tool that uses OpenAI Vision API to extract parcel information from maps and integrates with Regrid API for boundary data.

## Features

- 🗺️ **Image Upload**: Support for PNG, JPEG, PDF, and TIFF parcel maps
- 📍 **Coordinate Input**: Direct coordinate processing for parcel lookup
- 🤖 **AI-Powered**: Uses OpenAI o4-mini-vision for intelligent text extraction
- 🌐 **Interactive Maps**: Leaflet-based map visualization
- 🚀 **Local-First**: Runs entirely on your machine
- 📱 **Modern UI**: Clean, responsive web interface

## Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/HansenHomeAI/RegridParcelBoundaries.git
   cd RegridParcelBoundaries
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up environment variables**:
   - Copy `.env.example` to `.env` (if needed)
   - Add your API keys to `.env`:
     ```
     OPENAI_API_KEY=your_openai_key_here
     REGRID_API_KEY=your_regrid_key_here
     ```

### Usage

#### Web Interface (Recommended)

Start the web server:
```bash
poetry run parcelizer serve
```

Then open http://127.0.0.1:8080 in your browser.

#### Command Line

Process a parcel map image:
```bash
poetry run parcelizer process path/to/your/parcel-map.png
```

Process coordinates:
```bash
poetry run parcelizer coords "37.7749, -122.4194"
```

## Example Files

- `LOT 2 324 Dolan Rd Aerial Map.pdf` - Example parcel boundary map
- `elkins tract 2 use this one.pdf` - Second example parcel boundary map

## Tech Stack

- **Backend**: Python 3.11+, Flask, Poetry
- **AI**: OpenAI o4-mini-vision API
- **Maps**: Leaflet.js with OpenStreetMap tiles
- **Processing**: Pillow, pytesseract, shapely, geopandas
- **Async**: httpx with asyncio for concurrent API calls

## Development

Run in development mode:
```bash
poetry run parcelizer serve --debug
```

Run tests:
```bash
poetry run pytest
```

## License

MIT License 