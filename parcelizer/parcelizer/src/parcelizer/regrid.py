"""Client for Regrid Parcel API v2."""
from __future__ import annotations

import os
from pathlib import Path

import httpx

REGRID_URL = "https://api.regrid.com/v2/parcels"
REGRID_API_KEY = os.getenv("REGRID_API_KEY", "")


async def fetch_by_apn(apn: str, client: httpx.AsyncClient):
    """Fetch parcel geometry by APN."""
    params = {"apn": apn, "token": REGRID_API_KEY}
    resp = await client.get(f"{REGRID_URL}/apn", params=params)
    resp.raise_for_status()
    from shapely.geometry import shape
    geojson = resp.json()["features"][0]["geometry"]
    return shape(geojson)


async def fetch_by_address(address: str, client: httpx.AsyncClient):
    """Fetch parcel geometry by address."""
    params = {"address": address, "token": REGRID_API_KEY}
    resp = await client.get(f"{REGRID_URL}/address", params=params)
    resp.raise_for_status()
    from shapely.geometry import shape
    geojson = resp.json()["features"][0]["geometry"]
    return shape(geojson)
