import requests
from fastapi import HTTPException
from app.config import settings

ORS_GEOCODING_URL = "https://api.openrouteservice.org/geocode/search"


def geocodifica_citta(nome_citta: str) -> tuple[float, float]:
    
    #Restituisce (lon, lat) della città usando OpenRouteService.
    

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


def reverse_geocoding(lat: float, lon: float) -> str:
    """
    Restituisce la città/paese più vicino usando Nominatim (OpenStreetMap).
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 10,
        "addressdetails": 1
    }

    try:
        r = requests.get(url, params=params, headers={"User-Agent": "roadtrip-app"}, timeout=5)
        if r.status_code != 200:
            return "Località sconosciuta"

        data = r.json()
        addr = data.get("address", {})

        return (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality")
            or "Località sconosciuta"
        )

    except Exception:
        return "Località sconosciuta"
