import requests
from fastapi import HTTPException
from app.config import settings

ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"


def calcola_percorso(start_lon: float, start_lat: float, end_lon: float, end_lat: float) -> dict:
    print(">>> calcola_percorso <<<")

    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            [start_lon, start_lat],
            [end_lon, end_lat]
        ],
        "instructions": False,
        "geometry": True 
    }

    response = requests.post(ORS_DIRECTIONS_URL, json=body, headers=headers)

    print("STATUS ORS:", response.status_code)
    print("TESTO ORS:", response.text[:500])

    try:
        data = response.json()
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"ORS ha restituito una risposta non JSON: {response.text}"
        )

    if "features" not in data or not data["features"]:
        raise HTTPException(
            status_code=502,
            detail=f"Formato ORS inatteso o features vuoto: {data}"
        )

    feature = data["features"][0]
    summary = feature["properties"]["summary"]

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
        "geometry": geometry
    }
