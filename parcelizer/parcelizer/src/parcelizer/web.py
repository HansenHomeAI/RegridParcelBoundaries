"""Flask web UI for Parcelizer."""
from __future__ import annotations

import asyncio
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
import httpx

from .ocr import extract_text
from .vision import extract_metadata
from .regrid import fetch_by_apn, fetch_by_address
from .utils import save_geojson, save_vertices


template = """
<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Parcelizer</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
<h1>Parcelizer</h1>
<form id="form"><input type="file" name="file" id="file" /></form>
<div id="map" style="height:500px"></div>
<script>
const fileInput = document.getElementById('file');
fileInput.onchange = async () => {
  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  const res = await fetch('/process', {method: 'POST', body: fd});
  const data = await res.json();
  const map = L.map('map').setView([0,0],1);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution:'© OSM'}).addTo(map);
  const geo = L.geoJSON(data.geojson).addTo(map);
  map.fitBounds(geo.getBounds());
};
</script>
</body></html>
"""


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        return render_template_string(template)

    @app.post("/process")
    async def process() -> tuple[str, int]:
        file = request.files["file"]
        path = Path("/tmp") / file.filename
        file.save(path)
        text = extract_text(path)
        metadata = await extract_metadata(path, text)
        async with httpx.AsyncClient() as client:
            if "parcel_id" in metadata:
                geom = await fetch_by_apn(metadata["parcel_id"], client)
            else:
                geom = await fetch_by_address(metadata.get("address", ""), client)
        save_geojson(metadata.get("parcel_id", "unknown"), geom)
        save_vertices(metadata.get("parcel_id", "unknown"), geom)
        return jsonify({"geojson": {"type": "Feature", "geometry": geom.__geo_interface__}}), 200

    return app


def main() -> None:
    app = create_app()
    app.run(port=8080, debug=True)

if __name__ == "__main__":
    main()
