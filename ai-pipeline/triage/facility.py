"""
Nearest health facility lookup using OpenStreetMap's Overpass API,
with a static fallback list for demo reliability.
Only overpass.kumi.systems is reachable from Render's network per
production logs (other public mirrors returned hard connection failures).
"""
import requests

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "WehaHealth/1.0 (Sahara CodeSwitch Africa Challenge submission)"}

# Fallback facilities used only if the live Overpass lookup fails or
# times out. This guarantees the feature still works on camera even
# if Overpass is slow or down at the exact moment you're recording.
FALLBACK_FACILITIES = {
    "abuja": {
        "name": "National Hospital Abuja",
        "lat": 9.0579,
        "lng": 7.4951,
        "maps_link": "https://www.openstreetmap.org/?mlat=9.0579&mlon=7.4951#map=17/9.0579/7.4951"
    },
    "lagos": {
        "name": "Lagos University Teaching Hospital (LUTH)",
        "lat": 6.5167,
        "lng": 3.3833,
        "maps_link": "https://www.openstreetmap.org/?mlat=6.5167&mlon=3.3833#map=17/6.5167/3.3833"
    },
    "accra": {
        "name": "Korle Bu Teaching Hospital",
        "lat": 5.5361,
        "lng": -0.2278,
        "maps_link": "https://www.openstreetmap.org/?mlat=5.5361&mlon=-0.2278#map=17/5.5361/-0.2278"
    },
    "addis_ababa": {
        "name": "Tikur Anbessa Specialized Hospital",
        "lat": 9.0333,
        "lng": 38.7500,
        "maps_link": "https://www.openstreetmap.org/?mlat=9.0333&mlon=38.7500#map=17/9.0333/38.7500"
    }
}
DEFAULT_FALLBACK_KEY = "abuja"


def geocode_place_name(place_name: str) -> dict:
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": place_name, "format": "json", "limit": 1},
            headers=HEADERS,
            timeout=8
        )
        results = response.json()
        if not results:
            return None
        return {"lat": float(results[0]["lat"]), "lng": float(results[0]["lon"])}
    except Exception as e:
        print(f"[facility] Geocoding failed: {e}")
        return None


def _query_overpass(lat: float, lng: float, radius_m: int, timeout_s: int) -> dict:
    query = f"""
    [out:json][timeout:{timeout_s - 2}];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lng});
      node["amenity"="clinic"](around:{radius_m},{lat},{lng});
    );
    out center 3;
    """
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=timeout_s)
        data = response.json()
        elements = data.get("elements", [])
        if not elements:
            return None

        facility = elements[0]
        name = facility.get("tags", {}).get("name", "Unnamed health facility")
        facility_lat = facility.get("lat")
        facility_lng = facility.get("lon")

        return {
            "name": name,
            "lat": facility_lat,
            "lng": facility_lng,
            "maps_link": f"https://www.openstreetmap.org/?mlat={facility_lat}&mlon={facility_lng}#map=17/{facility_lat}/{facility_lng}"
        }
    except Exception as e:
        print(f"[facility] Overpass lookup failed: {e}")
        return None


def find_nearest_facility(lat: float, lng: float, radius_m: int = 8000, fallback_key: str = DEFAULT_FALLBACK_KEY) -> dict:
    # Single fast attempt — no blocking retry. Leaves plenty of room
    # inside node's 45s intake budget alongside transcription,
    # extraction, and escalation.
    result = _query_overpass(lat, lng, radius_m, timeout_s=10)
    if result is not None:
        return result

    print(f"[facility] Live lookup failed, using static fallback for '{fallback_key}'")
    fallback = FALLBACK_FACILITIES.get(fallback_key, FALLBACK_FACILITIES[DEFAULT_FALLBACK_KEY])
    return dict(fallback, name=f"{fallback['name']} (nearest known facility)")