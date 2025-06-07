#!/usr/bin/env python3
"""Test script for Regrid API debugging."""

import asyncio
import httpx
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_regrid_api():
    """Test the Regrid API with various queries."""
    
    api_key = os.getenv("REGRID_API_KEY")
    if not api_key:
        print("Error: REGRID_API_KEY not found in environment")
        return
    
    base_url = "https://app.regrid.com/api/v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test with correct parameter names
    test_cases = [
        # Test the corrected endpoints
        ("/parcels/apn", {"parcelnumb": "2006161255"}),
        ("/parcels/apn", {"parcelnumb": "050400150400"}),
        ("/parcels/address", {"query": "324 Dolan Rd"}),
        ("/parcels/address", {"query": "324 Dolan Rd", "state": "WA"}),
        ("/parcels/address", {"query": "1501 Canyon Creek Rd"}),
        
        # Test some known addresses that might be in the database
        ("/parcels/address", {"query": "1600 Pennsylvania Avenue"}),
        ("/parcels/address", {"query": "1 Infinite Loop, Cupertino, CA"}),
    ]
    
    async with httpx.AsyncClient() as client:
        for i, (endpoint, params) in enumerate(test_cases):
            print(f"\n--- Test {i+1} ---")
            print(f"Endpoint: {endpoint}")
            print(f"Params: {params}")
            
            try:
                url = f"{base_url}{endpoint}"
                response = await client.get(url, headers=headers, params=params)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    if "parcels" in data:
                        parcels = data["parcels"]
                        print(f"Parcels type: {type(parcels)}")
                        
                        if isinstance(parcels, dict):
                            print(f"Parcels dict keys: {list(parcels.keys())}")
                            # Show first few items
                            for i, (key, value) in enumerate(parcels.items()):
                                if i < 3:  # Show first 3 items
                                    print(f"  {key}: {type(value)} - {str(value)[:100]}...")
                        elif isinstance(parcels, list):
                            print(f"Found {len(parcels)} parcels in list")
                            if parcels:
                                parcel = parcels[0]
                                print(f"First parcel type: {type(parcel)}")
                                if isinstance(parcel, dict):
                                    print(f"First parcel keys: {list(parcel.keys())}")
                        else:
                            print(f"Unexpected parcels type: {type(parcels)}")
                    elif "features" in data:
                        print(f"Found {len(data.get('features', []))} features")
                        if data.get('features'):
                            feature = data['features'][0]
                            props = feature.get('properties', {})
                            print(f"First result: {props.get('address', 'No address')} (APN: {props.get('apn', 'No APN')})")
                    else:
                        print(f"No parcels or features found")
                elif response.status_code == 404:
                    print("No parcels found (404)")
                elif response.status_code == 401:
                    print("Unauthorized (401) - Check API key")
                elif response.status_code == 403:
                    print("Forbidden (403) - Check API permissions")
                else:
                    print(f"Error: {response.text}")
                    
            except Exception as e:
                print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_regrid_api()) 