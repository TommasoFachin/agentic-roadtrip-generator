import requests
from fastapi import HTTPException

def geocoding_citta(nome_citta: str) -> tuple[float, float]:
    """
    Restituisce (lon, lat) del centro città usando Nominatim.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": nome_citta,
        "format": "json",
        "limit": 1
    }

    # Nominatim richiede un User-Agent specifico. Se è troppo generico o usato da troppi utenti,
    # il servizio risponde con 403 (Forbidden). Usane uno unico per il tuo progetto.
    headers = {"User-Agent": "RoadTripGenerator-UniProject-Tommaso/1.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        
        if r.status_code != 200:
            # Stampiamo nel terminale il vero errore per capire se siamo bloccati
            print(f"DEBUG GEOCoding: Nominatim ha risposto con {r.status_code} - {r.text}")
            raise HTTPException(
                status_code=502,
                detail=f"Errore servizio geocoding (Status: {r.status_code})"
            )
            
        data = r.json()
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"Impossibile trovare coordinate per: {nome_citta}"
            )

        item = data[0]
        return float(item["lon"]), float(item["lat"])
    except requests.exceptions.RequestException as e:
        print(f"DEBUG GEOCoding: Errore di rete: {e}")
        raise HTTPException(status_code=503, detail="Servizio di geocodifica non raggiungibile")


def reverse_geocoding(lat: float, lon: float) -> str:
    """
    Restituisce la città/paese più vicino usando Nominatim.
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
        headers = {"User-Agent": "RoadTripGenerator-UniProject-Tommaso/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
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
