import requests
from fastapi import HTTPException
from app.config import settings

ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


def calcola_percorso(start_lon: float, start_lat: float, end_lon: float, end_lat: float) -> dict:
    print(">>> VERSIONE CORRETTA DI calcola_percorso <<<")

    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
    "coordinates": [
        [start_lon, start_lat],
        [end_lon, end_lat]
    ],
    "format": "geojson"
}

    response = requests.post(ORS_DIRECTIONS_URL, json=body, headers=headers)

    data = response.json()

    # Debug temporaneo
    #print("RISPOSTA ORS:", data)

    # Controllo formato corretto
    if "routes" not in data or not data["routes"]:
        raise HTTPException(
            status_code=502,
            detail=f"Formato ORS inatteso o routes vuoto: {data}"
        )

    summary = data["routes"][0]["summary"]

    return {
        "distanza_km": summary["distance"] / 1000,
        "durata_sec": summary["duration"],
    }
