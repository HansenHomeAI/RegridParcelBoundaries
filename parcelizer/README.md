# Parcelizer

Local-first tool to extract parcel boundaries from images using OpenAI vision and Regrid API.

## Installation

```bash
# Requires Python 3.11 and Poetry
poetry install
```

## Usage

CLI:

```bash
poetry run parcelizer path/to/parcel_image.png
```

Web UI:

```bash
poetry run python -m parcelizer.web
```

Then open <http://127.0.0.1:8080> in your browser.
