"""Demo data for testing the parcelizer pipeline."""

from typing import Dict, Any

# Sample parcel boundary data for demonstration
DEMO_PARCELS = {
    "324 Dolan Rd": {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-122.8, 46.1],
                [-122.799, 46.1],
                [-122.799, 46.101],
                [-122.8, 46.101],
                [-122.8, 46.1]
            ]]
        },
        "properties": {
            "parcel_id": "324_DOLAN_RD",
            "apn": "123456789",
            "address": "324 Dolan Rd",
            "county": "Cowlitz",
            "state": "WA"
        }
    },
    "2006161255": {
        "type": "Feature", 
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-121.5, 45.8],
                [-121.499, 45.8],
                [-121.499, 45.801],
                [-121.5, 45.801],
                [-121.5, 45.8]
            ]]
        },
        "properties": {
            "parcel_id": "SKAMANIA_2006161255",
            "apn": "2006161255",
            "address": "Pleasant Rd",
            "county": "Skamania",
            "state": "WA"
        }
    },
    "050400150400": {
        "type": "Feature",
        "geometry": {
            "type": "Polygon", 
            "coordinates": [[
                [-121.4, 45.7],
                [-121.399, 45.7],
                [-121.399, 45.701],
                [-121.4, 45.701],
                [-121.4, 45.7]
            ]]
        },
        "properties": {
            "parcel_id": "SKAMANIA_050400150400",
            "apn": "050400150400",
            "address": "1501 Canyon Creek Rd",
            "county": "Skamania",
            "state": "WA"
        }
    }
}


def get_demo_parcel_response(identifier: str) -> Dict[str, Any]:
    """Get demo parcel response for testing."""
    # Try to find a matching demo parcel
    demo_parcel = None
    
    # Check for exact matches first
    if identifier in DEMO_PARCELS:
        demo_parcel = DEMO_PARCELS[identifier]
    else:
        # Check for partial matches in address or APN
        for key, parcel in DEMO_PARCELS.items():
            props = parcel["properties"]
            if (identifier.lower() in props.get("address", "").lower() or
                identifier in props.get("apn", "") or
                any(word in props.get("address", "").lower() for word in identifier.lower().split())):
                demo_parcel = parcel
                break
    
    if demo_parcel:
        return {
            "parcels": {
                "type": "FeatureCollection",
                "features": [demo_parcel]
            },
            "buildings": {"type": "FeatureCollection", "features": []},
            "zoning": {"type": "FeatureCollection", "features": []}
        }
    else:
        return {
            "parcels": {"type": "FeatureCollection", "features": []},
            "buildings": {"type": "FeatureCollection", "features": []},
            "zoning": {"type": "FeatureCollection", "features": []}
        } 