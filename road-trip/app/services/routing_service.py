# questo file si occupa di interfacciarsi con l’API di OpenRouteService per calcolare
# il percorso reale tra due coordinate, restituendo distanza, durata e geometria del percorso.

import requests
from fastapi import HTTPException
from app.config import settings
from typing import List, Tuple

ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"


def calcola_percorso(coordinate_viaggio: List[Tuple[float, float]]) -> dict:
    print(">>> calcola_percorso <<<")

    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [[lon, lat] for lon, lat in coordinate_viaggio],
        "instructions": False,
        "geometry": True 
    }

    #chiamata HTTP POST a ORS
    try:
        response = requests.post(ORS_DIRECTIONS_URL, json=body, headers=headers, timeout=45)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Errore di rete durante la chiamata a ORS: {e}"
        )

    try:
        data = response.json()   #parsing json
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"ORS ha restituito una risposta non JSON: {response.text}"
        )
        
    if "error" in data:
        raise HTTPException(
            status_code=502,
            detail=f"Errore API ORS: {data['error'].get('message', data['error'])}"
        )

    if "features" not in data or not data["features"]:
        raise HTTPException(
            status_code=502,
            detail=f"Formato ORS inatteso o features vuoto: {data}"
        )

    feature = data["features"][0]
    summary = feature["properties"]["summary"]
    way_points = feature["properties"].get("way_points", [])

    # Geometria corretta (lista di coordinate)
    geometry = feature.get("geometry", {}).get("coordinates", None)

    if not geometry:
        raise HTTPException(
            status_code=502,
            detail=f"ORS non ha restituito una geometria valida: {feature.get('geometry')}"
        )

    return {
        "distanza_km": summary["distance"] / 1000,
        "durata_sec": summary["duration"],
        "geometry": geometry,
        "way_points": way_points
    }
