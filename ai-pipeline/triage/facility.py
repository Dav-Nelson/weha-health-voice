"""
Nearest health facility lookup using free OpenStreetMap services.
Tries multiple Overpass mirrors since some hosts may be unreachable
from certain hosting providers' networks (observed on Render free tier).
"""
import requests

OVERPASS_MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "WehaHealth/1.0 (Sahara CodeSwitch Africa Challenge submission)"}


def geocode_place_name(place_name: str) -> dict:
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": place_name, "format": "json", "limit": 1},
            headers=HEADERS,
            timeout=10
        )
        results = response.json()
        if not results:
            return None
        return {"lat": float(results[0]["lat"]), "lng": float(results[0]["lon"])}
    except Exception as e:
        print(f"[facility] Geocoding failed: {e}")
        return None


def _query_overpass(lat: float, lng: float, radius_m: int) -> dict:
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lng});
      node["amenity"="clinic"](around:{radius_m},{lat},{lng});
      way["amenity"="hospital"](around:{radius_m},{lat},{lng});
      way["amenity"="clinic"](around:{radius_m},{lat},{lng});
    );
    out center 5;
    """
    for mirror in OVERPASS_MIRRORS:
        try:
            response = requests.post(mirror, data={"data": query}, headers=HEADERS, timeout=15)
            data = response.json()
            elements = data.get("elements", [])
            if not elements:
                continue

            facility = elements[0]
            name = facility.get("tags", {}).get("name", "Unnamed health facility")
            facility_lat = facility.get("lat") or facility.get("center", {}).get("lat")
            facility_lng = facility.get("lon") or facility.get("center", {}).get("lon")

            return {
                "name": name,
                "lat": facility_lat,
                "lng": facility_lng,
                "maps_link": f"https://www.openstreetmap.org/?mlat={facility_lat}&mlon={facility_lng}#map=17/{facility_lat}/{facility_lng}"
            }
        except Exception as e:
            print(f"[facility] Overpass mirror {mirror} failed: {e}")
            continue
    return None


def find_nearest_facility(lat: float, lng: float, radius_m: int = 5000) -> dict:
    result = _query_overpass(lat, lng, radius_m)
    if result is None:
        result = _query_overpass(lat, lng, 15000)
    return result