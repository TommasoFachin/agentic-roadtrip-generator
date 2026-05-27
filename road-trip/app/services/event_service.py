# questo file si occupa di cercare eventi tramite l'API di Ticketmaster

import requests
from datetime import datetime
from app.config import settings

def mappa_interessi_eventi(interessi: list) -> list:
    """Mappa gli interessi generici dell'utente a classificazioni di Ticketmaster."""
    mapping = {
        "musica": "Music",
        "concerto": "Music",
        "festival": "Music",
        "sport": "Sports",
        "partita": "Sports",
        "teatro": "Arts & Theatre",
        "spettacolo": "Arts & Theatre",
        "mostra": "Arts & Theatre",
        "arte": "Arts & Theatre",
        "famiglia": "Family",
        "bambini": "Family",
    }
    classifications = set()
    for interesse in interessi:
        if interesse.lower() in mapping:
            classifications.add(mapping[interesse.lower()])
    return list(classifications)

def cerca_eventi(citta: str, data: datetime.date, interessi: list) -> list:
    """Cerca eventi su Ticketmaster per una data città e data, basandosi sugli interessi."""
    if not settings.TICKETMASTER_API_KEY:
        print("   > ATTENZIONE: TICKETMASTER_API_KEY non configurata. Salto ricerca eventi.")
        return []

    print(f"   > Ricerca eventi per {citta} il {data}...")

    start_date = datetime.combine(data, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date = datetime.combine(data, datetime.max.time()).strftime('%Y-%m-%dT%H:%M:%SZ')

    classifications = mappa_interessi_eventi(interessi)
    # NON usiamo "keyword" con gli interessi italiani o frasi miste, altrimenti Ticketmaster non trova nulla!

    params = {
        "apikey": settings.TICKETMASTER_API_KEY,
        "city": citta.split(",")[0].strip(),
        "startDateTime": start_date,
        "endDateTime": end_date,
        "sort": "date,asc",
        "size": 20
    }

    if classifications:
        params["classificationName"] = ",".join(classifications)

    url = "https://app.ticketmaster.com/discovery/v2/events.json"

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        eventi_trovati = data.get("_embedded", {}).get("events", [])
        print(f"     Trovati {len(eventi_trovati)} eventi.")
        return eventi_trovati
    except Exception as e:
        print(f"     Eccezione durante la chiamata a Ticketmaster: {e}")
        return []