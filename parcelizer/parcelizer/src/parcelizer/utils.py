"""Utility helpers for Parcelizer."""
from __future__ import annotations

from pathlib import Path
import csv
import json

def _mapping(geometry):
    """Return GeoJSON mapping for ``geometry`` without importing globally."""
    from shapely.geometry import mapping
    return mapping(geometry)


OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def save_geojson(parcel_id: str, geometry) -> Path:
    """Save geometry to a GeoJSON file in ``OUTPUT_DIR``.

    Parameters
    ----------
    parcel_id:
        Identifier for file naming.
    geometry:
        Shapely geometry object.
    Returns
    -------
    Path to the saved file.
    """
    path = OUTPUT_DIR / f"{parcel_id}.geojson"
    with path.open("w", encoding="utf-8") as fh:
        json.dump({"type": "Feature", "geometry": _mapping(geometry)}, fh)
    return path


def save_vertices(parcel_id: str, geometry) -> Path:
    """Save vertices of ``geometry`` to CSV in ``OUTPUT_DIR``."""
    path = OUTPUT_DIR / f"{parcel_id}_vertices.csv"
    coords = list(geometry.exterior.coords)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["lat", "lon"])
        for lon, lat in coords:
            writer.writerow([lat, lon])
    return path
