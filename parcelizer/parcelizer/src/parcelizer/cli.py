"""CLI entry point for Parcelizer."""
from __future__ import annotations

import asyncio
from argparse import ArgumentParser
from pathlib import Path

import httpx

from .ocr import extract_text
from .vision import extract_metadata
from .regrid import fetch_by_apn, fetch_by_address
from .utils import save_geojson, save_vertices


async def run(path: Path) -> None:
    text = extract_text(path)
    metadata = await extract_metadata(path, text)
    async with httpx.AsyncClient() as client:
        if "parcel_id" in metadata:
            geom = await fetch_by_apn(metadata["parcel_id"], client)
        else:
            geom = await fetch_by_address(metadata.get("address", ""), client)
    parcel_id = metadata.get("parcel_id", "unknown")
    save_geojson(parcel_id, geom)
    save_vertices(parcel_id, geom)
    print(f"Saved parcel {parcel_id}")


def main() -> None:
    parser = ArgumentParser(description="Parcelizer CLI")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    asyncio.run(run(args.file))

if __name__ == "__main__":
    main()
