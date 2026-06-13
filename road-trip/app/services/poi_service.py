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
def cerca_poi(lat, lon, radius=30000, kinds=None, limit=100, min_rate=None):
    params = {
        "apikey": OPENTRIPMAP_API_KEY,
        "radius": radius,
        "lon": lon,
        "lat": lat,
        "limit": limit,
        "orderby": "distance",
        "format": "json",
    }

    if kinds:
        params["kinds"] = ",".join(set(kinds))
        
    if min_rate:
        params["rate"] = min_rate


    url = f"{BASE_URL}/radius"

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException:
        return []

    if response.status_code != 200:
        print(f"     [OpenTripMap] Errore API: {response.status_code} - {response.text}")
        return []

    data = response.json()

    blacklist = ["accomodations", "unclassified_objects"]

    poi_list = []
    for item in data:
        name = item.get("name", "").strip()
        kinds = item.get("kinds", "")

        if not name:
            continue

        if any(b in kinds for b in blacklist):
            continue

        poi_list.append({
            "name": name,
            "kind": kinds,
            "dist": item.get("dist", 0),
            "rate": item.get("rate", 0),
            "lat": item.get("point", {}).get("lat"),
            "lon": item.get("point", {}).get("lon")
        })

    return poi_list


def cerca_strutture(lat, lon, kind="accomodations", radius=15000, limit=40):
    """
    Cerca hotel o ristoranti in base alla categoria richiesta.
    kind: "accomodations" oppure "foods"
    """
    params = {
        "apikey": OPENTRIPMAP_API_KEY,
        "radius": radius,
        "lon": lon,
        "lat": lat,
        "kinds": kind,
        "limit": limit,
        "orderby": "distance",
        "format": "json",
    }
    url = f"{BASE_URL}/radius"
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            strutture = []
            nomi_visti = set()
            for item in data:
                name = item.get("name", "").strip()
                if name and name not in nomi_visti:
                    nomi_visti.add(name)
                    strutture.append({
                        "name": name,
                        "rate": item.get("rate", 0),
                        "lat": item.get("point", {}).get("lat"),
                        "lon": item.get("point", {}).get("lon")
                    })
            return strutture
    except Exception as e:
        print(f"     [OpenTripMap] Errore API strutture ({kind}): {e}")
    return []


# funzione che mappa gli interessi dell’utente alle categorie di OpenTripMap, 
# restituendo una lista di categorie da usare nella ricerca dei POI.
def mappa_interessi(interessi_poi):
    """
    Mappa gli interessi dell’utente alle categorie OpenTripMap.
    Versione PRO: supporta interessi in italiano e restituisce kinds utili
    per ottenere POI iconici e turistici.
    """

    mapping = {
        # SPORT E DIVERTIMENTO
        "sport": ["sport"],
        "musica": ["cultural", "amusements"],
        "birra": ["foods"],

        # CIBO
        "cibo": ["foods"],

        # NATURA
        "natura": ["natural"],

        # CITTÀ / CENTRO
        "città": ["urban_environment", "squares", "interesting_places"],
        "centro": ["urban_environment", "squares"],
        "piazze": ["squares", "urban_environment"],

        # ARTE / CULTURA
        "arte": ["cultural", "museums"],
        "cultura": ["cultural", "museums"],
        "musei": ["museums", "cultural"],
        "museo": ["museums", "cultural"],

        # STORIA / MONUMENTI
        "storia": ["historic", "monuments_and_memorials"],
        "storico": ["historic", "monuments_and_memorials"],
        "monumenti": [
            "monuments_and_memorials",
            "historic",
            "architecture",
            "interesting_places",
            "cultural"
        ],

        "punti di interesse": [
            "interesting_places",
            "tourist_facilities",
            "architecture",
            "historic",
            "cultural",
            "museums"
        ],

        "centro città": [
            "urban_environment",
            "squares",
            "interesting_places",
            "historic",
            "architecture",
            "cultural"
        ],
        "monumento": ["monuments_and_memorials", "historic"],
        "centri città": ["urban_environment", "squares", "interesting_places", "historic", "architecture", "cultural"],
        "guerra": ["historic", "monuments_and_memorials"],

        # ARCHITETTURA
        "architettura": ["architecture"],
        "edifici": ["architecture"],
        "palazzi": ["architecture", "historic"],

        # INTERESSI GENERICI TURISTICI
        
        "punti d'interesse": ["interesting_places", "tourist_facilities"],
        "famosi": ["interesting_places", "historic", "cultural"],
        "iconici": ["interesting_places", "historic", "cultural"],
        "turistici": ["interesting_places", "historic", "cultural"],

        # RELIGIONE (solo se richiesto)
        "chiese": ["religion"],
        "religione": ["religion"],
        "cattedrali": ["religion"],
    }

    kinds = []
    for interesse in interessi_poi:
        interesse_lower = interesse.lower().strip().replace("_", " ")
        if interesse_lower in mapping:
            kinds.extend(mapping[interesse_lower])
        else:
            # Ricerca parziale salvavita per intercettare sinonimi o errori
            for key in mapping:
                if key in interesse_lower or interesse_lower in key:
                    kinds.extend(mapping[key])
                    break

    # fallback intelligente se l’utente mette qualcosa di non mappato
    if not kinds and interessi_poi:
        kinds = [
            "historic",
            "monuments_and_memorials",
            "cultural",
            "museums",
            "architecture",
            "urban_environment",
            "squares",
            "interesting_places"
        ]

    # rimuovi duplicati mantenendo ordine
    return list(dict.fromkeys(kinds))
