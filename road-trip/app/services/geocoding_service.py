import requests
from fastapi import HTTPException
from app.config import settings

ORS_GEOCODING_URL = "https://api.openrouteservice.org/geocode/search"


def geocodifica_citta(nome_citta: str) -> tuple[float, float]:
    """
    Restituisce (lon, lat) della città usando OpenRouteService.
    """

    params = {
        "api_key": settings.ORS_API_KEY,
        "text": nome_citta,
        "size": 1
    }

    response = requests.get(ORS_GEOCODING_URL, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Errore ORS geocoding: {response.status_code} - {response.text}"
        )

    data = response.json()

    try:
        feature = data["features"][0]
        lon, lat = feature["geometry"]["coordinates"]
    except (KeyError, IndexError):
        raise HTTPException(
            status_code=404,
            detail=f"Impossibile trovare coordinate per: {nome_citta}"
        )

    return lon, lat
