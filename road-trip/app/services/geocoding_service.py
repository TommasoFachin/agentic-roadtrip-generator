import requests
from fastapi import HTTPException
import time
from functools import lru_cache

@lru_cache(maxsize=128)
def geocoding_citta(nome_citta: str) -> tuple[float, float]:
    """
    Restituisce (lon, lat) del centro città usando l'API gratuita Photon (Komoot).
    Sostituisce Nominatim per evitare i severi blocchi 429.
    """
    url = "https://photon.komoot.io/api/"
    params = {
        "q": nome_citta,
        "limit": 1
    }

    headers = {"User-Agent": "RoadTripGenerator-UniProject-Tommaso/1.0"}

    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            
            if r.status_code != 200:
                print(f"DEBUG GEOCoding: Photon ha risposto con {r.status_code} - {r.text}")
                time.sleep(2.0)
                continue
                
            data = r.json()
            features = data.get("features", [])
            if not features:
                raise HTTPException(
                    status_code=404,
                    detail=f"Impossibile trovare coordinate per: {nome_citta}"
                )

            coords = features[0]["geometry"]["coordinates"]
            # Photon restituisce [lon, lat]
            return float(coords[0]), float(coords[1])
            
        except requests.exceptions.RequestException as e:
            print(f"DEBUG GEOCoding: Errore di rete: {e}")
            if attempt == 2:
                raise HTTPException(status_code=503, detail="Servizio di geocodifica non raggiungibile")
            time.sleep(2.0)

    raise HTTPException(status_code=502, detail="Errore servizio geocoding (Photon API)")

@lru_cache(maxsize=1024)
def reverse_geocoding(lat: float, lon: float) -> str:
    """
    Restituisce la città/paese più vicino usando l'API gratuita Photon (Komoot).
    """
    url = "https://photon.komoot.io/reverse"
    params = {
        "lat": round(lat, 3),
        "lon": round(lon, 3)
    }
    headers = {"User-Agent": "RoadTripGenerator-UniProject-Tommaso/1.0"}

    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            
            if r.status_code != 200:
                time.sleep(2.0)
                continue

            data = r.json()
            features = data.get("features", [])
            if not features:
                return "Località sconosciuta"

            props = features[0]["properties"]

            return (
                props.get("city")
                or props.get("town")
                or props.get("village")
                or props.get("name")
                or "Località sconosciuta"
            )

        except Exception:
            if attempt == 2:
                return "Località sconosciuta"
            time.sleep(2.0)
            
    return "Località sconosciuta"
