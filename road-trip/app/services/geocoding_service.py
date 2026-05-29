#questo file si occupa di geocodifica e reverse geocodifica usando l'API gratuita Photon (Komoot),

import requests
from fastapi import HTTPException
import time
from functools import lru_cache

@lru_cache(maxsize=128)
def geocoding_citta(nome_citta: str) -> tuple[float, float]:
    """
    Restituisce (lon, lat) del centro città.
    Usa Nominatim come primario perché supporta tutte le lingue (es. "Parigi" invece di "Paris").
    Usa Photon come fallback.
    """
    # Cambiamo User-Agent con un timestamp per evitare blocchi anti-spam di Nominatim
    headers = {
        "User-Agent": f"RoadTrip-Tommaso-{int(time.time())}@student.example.com",
        "Accept-Language": "it"
    }

    print(f"   > Cerco coordinate per: {nome_citta}...")

    # --- 1. PRIMARIO: NOMINATIM (Intelligente con le lingue) ---
    url_nominatim = "https://nominatim.openstreetmap.org/search"
    params_nominatim = {"q": nome_citta, "format": "json", "limit": 1}
    try:
        r = requests.get(url_nominatim, params=params_nominatim, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                # Nominatim restituisce lat e lon come stringhe
                lon, lat = float(data[0]["lon"]), float(data[0]["lat"])
                print(f"     [Nominatim] Trovato: {lat}, {lon}")
                return lon, lat
        else:
            print(f"     [Nominatim] Errore API: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"     [Nominatim] Eccezione: {e}")

    # --- 2. FALLBACK: PHOTON ---
    url_photon = "https://photon.komoot.io/api/"
    params_photon = {
        "q": nome_citta.split(",")[0].strip(),
        "limit": 1,
        "lang": "default"
    }

    try:
        r = requests.get(url_photon, params=params_photon, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            features = data.get("features", [])
            if features:
                coords = features[0]["geometry"]["coordinates"]
                lon, lat = float(coords[0]), float(coords[1])
                print(f"     [Photon] Trovato: {lat}, {lon}")
                return lon, lat
        else:
            print(f"     [Photon] Errore API: {r.status_code}")
    except Exception as e:
        print(f"     [Photon] Eccezione: {e}")

    raise HTTPException(status_code=404, detail=f"Impossibile trovare coordinate per: {nome_citta}")

@lru_cache(maxsize=1024)
def reverse_geocoding(lat: float, lon: float) -> tuple[str, str | None]:
    """
    Restituisce una tupla (città/paese, country_code) più vicini.
    Forza la ricerca su macro-aree (zoom 10 per Città, zoom 12 per Comuni grandi)
    per evitare di restituire frazioni o paesi sconosciuti a fine tappa.
    """
    headers = {"User-Agent": f"RoadTrip-Tommaso-{int(time.time())}@student.example.com"}

    # --- 1. PRIMARIO: NOMINATIM (Zoom decrescente espanso) ---
    url_nominatim = "https://nominatim.openstreetmap.org/reverse"
    
    # zoom 10 = City, zoom 12 = Town, zoom 14 = Village/Municipality
    for zoom in [10, 12, 14]:
        params_nominatim = {"lat": lat, "lon": lon, "format": "json", "zoom": zoom}
        try:
            r = requests.get(url_nominatim, params=params_nominatim, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                address = data.get("address", {})
                citta = (
                    address.get("city") or 
                    address.get("town") or 
                    address.get("municipality") or 
                    address.get("village") or
                    address.get("county")
                )
                country = address.get("country")
                country_code = address.get("country_code")
                if citta:
                    if country:
                        citta = f"{citta}, {country}"
                    return citta, country_code
        except Exception:
            time.sleep(0.5)
            
    # --- 2. FALLBACK SU PHOTON (Reverse geocoding corretto) ---
    url_photon = "https://photon.komoot.io/reverse"
    params_photon = {"lat": round(lat, 3), "lon": round(lon, 3), "limit": 1}
    try:
        r = requests.get(url_photon, params=params_photon, headers=headers, timeout=5)
        if r.status_code == 200:
            features = r.json().get("features", [])
            if features:
                props = features[0]["properties"]
                citta = props.get("city") or props.get("town") or props.get("village") or props.get("county") or props.get("name")
                country = props.get("country")
                country_code = props.get("countrycode")
                if citta:
                    if country:
                        citta = f"{citta}, {country}"
                    return citta, country_code
    except Exception:
        pass

    return "In viaggio", None
