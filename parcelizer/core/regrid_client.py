"""Regrid API client for fetching parcel boundary data."""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import httpx
from shapely.geometry import shape, Polygon
import geopandas as gpd

from .config import config
from .demo_data import get_demo_parcel_response


@dataclass
class ParcelBoundary:
    """Parcel boundary data from Regrid API."""
    parcel_id: str
    apn: Optional[str] = None
    address: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    geometry: Optional[Dict] = None  # GeoJSON geometry
    vertices: Optional[List[Tuple[float, float]]] = None  # [(lat, lon), ...]
    raw_response: Optional[Dict] = None


class RegridClient:
    """Client for Regrid Parcel API v2."""
    
    def __init__(self, demo_mode: bool = False) -> None:
        """Initialize the Regrid client."""
        self.base_url = "https://app.regrid.com/api/v2"
        self.headers = {
            "Authorization": f"Bearer {config.regrid_api_key}",
            "Content-Type": "application/json"
        }
        self.demo_mode = demo_mode
    
    async def search_by_apn(self, apn: str, county: Optional[str] = None, 
                           state: Optional[str] = None) -> Optional[ParcelBoundary]:
        """Search for parcel by APN (Assessor's Parcel Number)."""
        if self.demo_mode:
            print(f"🎭 Demo mode: Looking up APN {apn}")
            data = get_demo_parcel_response(apn)
            return self._parse_parcel_response(data, apn)
        
        try:
            async with httpx.AsyncClient() as client:
                # Clean up APN - remove any spaces or special characters
                clean_apn = ''.join(c for c in apn if c.isalnum())
                
                url = f"{self.base_url}/parcels/apn"
                params = {"parcelnumb": clean_apn}
                
                # Add county/state if available for better accuracy
                if county:
                    params["county"] = county.replace(" County", "").strip()
                if state:
                    params["state"] = state.strip()
                
                response = await client.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_parcel_response(data, apn)
                elif response.status_code == 404:
                    print(f"No parcel found for APN: {apn}")
                    return None
                else:
                    print(f"Regrid API error for APN {apn}: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error searching by APN {apn}: {e}")
            return None
    
    async def search_by_address(self, address: str, county: Optional[str] = None,
                               state: Optional[str] = None) -> Optional[ParcelBoundary]:
        """Search for parcel by address."""
        if self.demo_mode:
            print(f"🎭 Demo mode: Looking up address {address}")
            data = get_demo_parcel_response(address)
            return self._parse_parcel_response(data, address)
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/parcels/address"
                params = {"query": address}
                
                # Add county/state if available
                if county:
                    params["county"] = county.replace(" County", "").strip()
                if state:
                    params["state"] = state.strip()
                
                response = await client.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_parcel_response(data, address)
                elif response.status_code == 404:
                    print(f"No parcel found for address: {address}")
                    return None
                else:
                    print(f"Regrid API error for address {address}: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error searching by address {address}: {e}")
            return None
    
    def _parse_parcel_response(self, data: Dict, identifier: str) -> Optional[ParcelBoundary]:
        """Parse Regrid API response and extract parcel boundary."""
        try:
            # Regrid API v2 returns parcels as a GeoJSON FeatureCollection
            if "parcels" in data and isinstance(data["parcels"], dict):
                parcels_geojson = data["parcels"]
                
                if parcels_geojson.get("type") == "FeatureCollection":
                    features = parcels_geojson.get("features", [])
                    
                    if len(features) > 0:
                        feature = features[0]  # Take the first result
                        
                        geometry = feature.get("geometry")
                        properties = feature.get("properties", {})
                        
                        # Extract vertices from geometry
                        vertices = None
                        if geometry and geometry.get("type") == "Polygon":
                            coordinates = geometry.get("coordinates", [])
                            if coordinates:
                                # Get exterior ring coordinates (first array)
                                exterior_coords = coordinates[0]
                                # Convert from [lon, lat] to (lat, lon) tuples
                                vertices = [(coord[1], coord[0]) for coord in exterior_coords]
                        
                        return ParcelBoundary(
                            parcel_id=properties.get("parcel_id") or properties.get("id") or identifier,
                            apn=properties.get("apn") or properties.get("parcelnumb"),
                            address=properties.get("address") or properties.get("mail_address") or properties.get("situs_address"),
                            county=properties.get("county") or properties.get("county_name"),
                            state=properties.get("state") or properties.get("state_abbrev"),
                            geometry=geometry,
                            vertices=vertices,
                            raw_response=data
                        )
                    else:
                        print(f"No features found in parcels FeatureCollection for {identifier}")
                        return None
                else:
                    print(f"Parcels is not a FeatureCollection for {identifier}")
                    return None
            else:
                print(f"No parcels found in Regrid response for {identifier}")
                print(f"Response keys: {list(data.keys())}")
                return None
                
        except Exception as e:
            print(f"Error parsing Regrid response for {identifier}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def search_parcel(self, apn: Optional[str] = None, address: Optional[str] = None,
                           county: Optional[str] = None, state: Optional[str] = None) -> Optional[ParcelBoundary]:
        """Search for parcel using available identifiers (APN preferred, fallback to address)."""
        if apn:
            result = await self.search_by_apn(apn, county, state)
            if result:
                return result
        
        if address:
            return await self.search_by_address(address, county, state)
        
        return None
    
    def save_geojson(self, boundary: ParcelBoundary, output_path: str) -> None:
        """Save parcel boundary as GeoJSON file."""
        if not boundary.geometry:
            raise ValueError("No geometry data to save")
        
        geojson = {
            "type": "Feature",
            "geometry": boundary.geometry,
            "properties": {
                "parcel_id": boundary.parcel_id,
                "apn": boundary.apn,
                "address": boundary.address,
                "county": boundary.county,
                "state": boundary.state
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)
    
    def save_vertices_csv(self, boundary: ParcelBoundary, output_path: str) -> None:
        """Save parcel vertices as CSV file with header lat,lon."""
        if not boundary.vertices:
            raise ValueError("No vertices data to save")
        
        with open(output_path, 'w') as f:
            f.write("lat,lon\n")
            for lat, lon in boundary.vertices:
                f.write(f"{lat},{lon}\n") 