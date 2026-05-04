import requests
import math
import os

OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")
BASE_URL = "https://api.opentripmap.com/0.1/en/places"


def cerca_poi(lat, lon, radius=5000, kinds=None, limit=10):
    """
    Cerca POI reali usando OpenTripMap.
    kinds: lista di categorie (es. ["foods", "natural", "cultural"])
    """
    params = {
        "apikey": OPENTRIPMAP_API_KEY,
        "radius": radius,
        "lon": lon,
        "lat": lat,
        "limit": limit,
        "format": "json"
    }

    if kinds:
        params["kinds"] = ",".join(kinds)

    url = f"{BASE_URL}/radius"
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    data = response.json()

    poi_list = []
    for item in data:
        poi_list.append({
            "name": item.get("name", "Sconosciuto"),
            "kind": item.get("kinds", ""),
            "dist": item.get("dist", 0),
            "lat": item.get("point", {}).get("lat"),
            "lon": item.get("point", {}).get("lon")
        })

    return poi_list


def mappa_interessi(interessi):
    """
    Mappa gli interessi dell’utente alle categorie OpenTripMap.
    """
    mapping = {
        "cibo": ["foods", "restaurants", "cafes"],
        "natura": ["natural", "parks", "view_points"],
        "città": ["cultural", "architecture", "urban_environment"],
        "arte": ["museums", "theatres", "galleries"],
        "storia": ["historic", "monuments"]
    }

    kinds = []
    for interesse in interessi:
        if interesse in mapping:
            kinds.extend(mapping[interesse])

    return kinds
