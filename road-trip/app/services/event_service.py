# questo file si occupa di cercare eventi tramite l'API di Ticketmaster

import requests
from datetime import datetime
from app.config import settings

def mappa_interessi_eventi(interessi: list) -> dict:
    """
    Mappa gli interessi dell'utente a classificazioni e keyword per Ticketmaster.
    Restituisce un dizionario con 'classifications' e 'keywords'.
    """
    mapping_classificazioni = {
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
    
    # Mappiamo interessi specifici a keyword di ricerca, includendo traduzioni o sinonimi.
    keywords_map = {
        "birra": "birra beer sagra",
        "cibo": "cibo food sagra",
        "vino": "vino wine sagra",
        "sagra": "sagra festival",
    }

    classifications = set()
    keywords_set = set()

    for interesse in interessi:
        interesse_lower = interesse.lower().strip()
        
        # 1. Cerca nelle classificazioni
        if interesse_lower in mapping_classificazioni:
            classifications.add(mapping_classificazioni[interesse_lower])
        
        # 2. Cerca nelle keyword specifiche
        if interesse_lower in keywords_map:
            keywords_set.update(keywords_map[interesse_lower].split())
        # 3. Se non è una classificazione, usalo come keyword generica
        elif interesse_lower not in mapping_classificazioni:
            # Filtriamo interessi non pertinenti per eventi (es. 'storia')
            if interesse_lower not in ["monumenti", "storia", "architettura", "punti di interesse", "centro città"]:
                keywords_set.add(interesse_lower)

    return {
        "classifications": list(classifications),
        "keywords": list(keywords_set)
    }

def cerca_eventi(citta: str, data: datetime.date, interessi: list) -> list:
    """Cerca eventi su Ticketmaster per una data città e data, basandosi sugli interessi."""
    if not settings.TICKETMASTER_API_KEY:
        print("   > ATTENZIONE: TICKETMASTER_API_KEY non configurata. Salto ricerca eventi.")
        return []

    print(f"   > Ricerca eventi per {citta} il {data}...")

    start_date = datetime.combine(data, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date = datetime.combine(data, datetime.max.time()).strftime('%Y-%m-%dT%H:%M:%SZ')

    dati_ricerca = mappa_interessi_eventi(interessi)
    classifications = dati_ricerca["classifications"]
    keywords = dati_ricerca["keywords"]

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
    
    # Aggiungiamo le keyword alla ricerca. Ticketmaster le gestisce in OR.
    if keywords:
        params["keyword"] = " ".join(keywords)

    url = "https://app.ticketmaster.com/discovery/v2/events.json"

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        eventi_trovati = data.get("_embedded", {}).get("events", [])
        
        log_msg = f"     Trovati {len(eventi_trovati)} eventi."
        if classifications or keywords:
            log_msg += " Parametri usati:"
            if classifications:
                log_msg += f" Classificazioni='{', '.join(classifications)}'"
            if keywords:
                log_msg += f" Keywords='{' '.join(keywords)}'"
        print(log_msg)

        return eventi_trovati
    except Exception as e:
        print(f"     Eccezione durante la chiamata a Ticketmaster: {e}")
        return []