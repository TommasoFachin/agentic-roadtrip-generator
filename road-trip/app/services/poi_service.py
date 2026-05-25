# questo file si occupa di interfacciarsi con l’API di OpenTripMap per cercare POI popolari lungo il percorso,
# filtrando quelli meno rilevanti e mappando gli interessi dell’utente alle categorie di OpenTripMap.

import requests
import os
import re
from pathlib import Path

# --- CARICAMENTO SICURO CHIAVE API ---
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
OPENTRIPMAP_API_KEY = None
try:
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("OPENTRIPMAP_API_KEY"):
                OPENTRIPMAP_API_KEY = line.split("=", 1)[1].strip(" '\"\n")
                break
except FileNotFoundError:
    pass

if not OPENTRIPMAP_API_KEY:
    print("\n" + "="*80)
    print("⚠️ ATTENZIONE: OPENTRIPMAP_API_KEY non trovata nel file .env.")
    print("La ricerca dei Punti di Interesse (POI) non funzionerà.")
    print(f"Percorso del file .env cercato: {env_path}")
    print("="*80 + "\n")

BASE_URL = "https://api.opentripmap.com/0.1/en/places"

# funzione che, dato latitudine, longitudine e raggio, cerca POI popolari usando OpenTripMap,
#  filtrando quelli meno rilevanti e restituendo una lista di POI con nome, categoria, distanza
#  e coordinate.
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
    #chiamata HTTP GET a OpenTripMap API
    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Errore di rete OpenTripMap API: {e}")
        return []

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

        #costruzione lista POI da restituire
        poi_list.append({
            "name": name,
            "kind": kinds,
            "dist": item.get("dist", 0),
            "rate": item.get("rate", 0),
            "lat": item.get("point", {}).get("lat"),
            "lon": item.get("point", {}).get("lon")
        })

    return poi_list

# funzione che mappa gli interessi dell’utente alle categorie di OpenTripMap, 
# restituendo una lista di categorie da usare nella ricerca dei POI.
def mappa_interessi(interessi):
    """
    Mappa gli interessi dell’utente alle categorie OpenTripMap.
    """
    mapping = {
        "cibo": ["foods"],
        "natura": ["natural"],
        "città": ["cultural", "architecture", "interesting_places"],
        "arte": ["museums", "cultural"],
        "musei": ["museums"],  
        "storia": ["historic", "monuments_and_memorials"]
    }

    kinds = []
    for interesse in interessi:
        if interesse in mapping:
            kinds.extend(mapping[interesse])

    return list(set(kinds))
