import requests
import os
import re

OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")
BASE_URL = "https://api.opentripmap.com/0.1/en/places"


def cerca_poi(lat, lon, radius=8000, kinds=None, limit=20):
    """
    Cerca POI popolari usando OpenTripMap.
    Usa rate=3 e orderby=popularity per ottenere POI famosi.
    Filtra indirizzi e categorie inutili.
    """
    params = {
        "apikey": OPENTRIPMAP_API_KEY,
        "radius": radius,
        "lon": lon,
        "lat": lat,
        "limit": limit,
        "format": "json",
        "rate": "3",
        "orderby": "popularity"
    }

    if kinds:
        params["kinds"] = ",".join(set(kinds))

    url = f"{BASE_URL}/radius"
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Errore OpenTripMap API ({response.status_code}): {response.text}")
        return []

    data = response.json()

    # Filtri intelligenti
    address_pattern = re.compile(r'.*\s\d+')
    blacklist = ["accomodations", "urban_environment", "historic_districts", "unclassified_objects"]

    poi_list = []
    for item in data:
        name = item.get("name", "").strip()
        kinds = item.get("kinds", "")

        if not name or address_pattern.match(name):
            continue

        if any(b in kinds for b in blacklist):
            continue

        poi_list.append({
            "name": name,
            "kind": kinds,
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
        "cibo": ["foods"],
        "natura": ["natural"],
        "città": ["cultural", "architecture"],
        "arte": ["museums", "cultural"],
        "musei": ["museums"],  
        "storia": ["historic"]
    }

    kinds = []
    for interesse in interessi:
        if interesse in mapping:
            kinds.extend(mapping[interesse])

    return list(set(kinds))
