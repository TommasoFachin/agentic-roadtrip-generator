# questo file si occupa di cercare eventi tramite l'API di Ticketmaster

import requests
from datetime import datetime
from app.config import settings

def cerca_eventi_web(citta: str, data: datetime.date, country_code: str | None, interessi_eventi: list) -> list:
    """Effettua una ricerca sul web per trovare eventi usando DuckDuckGo, basati sugli interessi dell'utente."""
    try:
        from ddgs import DDGS
    except ImportError:
        print("   > [Web Search] Modulo 'ddgs' non installato. Esegui: pip install ddgs")
        return []

    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_nome = mesi_ita[data.month - 1]

    interessi_utili = interessi_eventi
    interessi_str = " ".join([i.lower() for i in interessi_eventi])

    # Costruiamo una query dinamica in base alla nazione per evitare spam SEO italiano all'estero
    is_italy = country_code and country_code.lower() == 'it'
    
    if is_italy:
        argomenti = " ".join(interessi_utili) if interessi_utili else "sagre festival"
        query = f"eventi {argomenti} {citta} {mese_nome} {data.year}"
    else:
        mese_eng = data.strftime("%B") # Traduce il mese in inglese (es. 'June')
        query = f"events festivals {citta} {mese_eng} {data.year}"
        # Aggiungiamo traduzioni manuali dei tuoi interessi chiave
        if "birra" in interessi_str: query += " beer"
        if "musica" in interessi_str: query += " music"
        if "sport" in interessi_str: query += " sport"

    print(f"   > [Web Search] Eseguo query: '{query}'...")

    # --- REGIONE DINAMICA ---
    # Se abbiamo il codice nazione (es. 'de'), lo usiamo per filtrare la ricerca (es. 'de-de')
    # Altrimenti, la ricerca è globale.
    region = None
    if country_code:
        region = f"{country_code.lower()}-{country_code.lower()}"

    risultati_web = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region=region, max_results=4))
            for r in results:
                risultati_web.append({
                    "name": r.get("title", "Senza titolo"),
                    "url": r.get("href", ""),
                    "classifications": [{
                        "segment": {"name": "Evento dal Web"},
                        "genre": {"name": "Interesse Specifico" if interessi_utili else "Generico"}
                    }]
                })
    except Exception as e:
        print(f"     [Web Search] Errore: {e}")
        
    return risultati_web

def mappa_interessi_eventi(interessi_eventi: list) -> dict:
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

    for interesse in interessi_eventi:
        interesse_lower = interesse.lower().strip()
        
        # 1. Cerca nelle classificazioni
        if interesse_lower in mapping_classificazioni:
            classifications.add(mapping_classificazioni[interesse_lower])
        
        # 2. Cerca nelle keyword specifiche
        if interesse_lower in keywords_map:
            keywords_set.update(keywords_map[interesse_lower].split())
        # 3. Se non è una classificazione, usalo come keyword generica
        elif interesse_lower not in mapping_classificazioni:
            keywords_set.add(interesse_lower)

    return {
        "classifications": list(classifications),
        "keywords": list(keywords_set)
    }

def cerca_eventi(citta: str, country_code: str | None, data: datetime.date, interessi_eventi: list) -> list:
    """
    Cerca eventi REALI entro 50 km usando:
    - Ticketmaster (radius)
    - Eventbrite (radius)
    - Bandsintown (radius, solo musica)
    - Web search (DuckDuckGo)
    Filtra per data e per interessi dell’utente.
    """

    print(f"   > Ricerca eventi per {citta} il {data}...")

    # --- COORDINATE DELLA TAPPA ---
    try:
        from app.services.geocoding_service import geocoding_citta
        lon, lat = geocoding_citta(citta)
    except:
        lon = lat = None

    data_str = data.strftime("%Y-%m-%d")
    eventi = []

    # --- 1️⃣ TICKETMASTER RADIUS 50 KM ---
    if settings.TICKETMASTER_API_KEY and lat and lon:
        try:
            url = "https://app.ticketmaster.com/discovery/v2/events.json"
            params = {
                "apikey": settings.TICKETMASTER_API_KEY,
                "latlong": f"{lat},{lon}",
                "radius": 50,
                "unit": "km",
                "startDateTime": f"{data_str}T00:00:00Z",
                "endDateTime": f"{data_str}T23:59:59Z"
            }
            r = requests.get(url, params=params).json()

            if "_embedded" in r:
                for e in r["_embedded"]["events"]:
                    try:
                        venue_name = e.get("_embedded", {}).get("venues", [{}])[0].get("name", "Unknown")
                    except Exception:
                        venue_name = "Unknown"
                    eventi.append({
                        "name": e.get("name", "Senza titolo"),
                        "url": e.get("url", ""),
                        "classifications": e.get("classifications", []),
                        "venue": venue_name
                    })

            print(f"     > Ticketmaster: trovati {len(eventi)} eventi radius.")
        except Exception as e:
            print("     > Errore Ticketmaster:", e)

    # --- 2️⃣ EVENTBRITE RADIUS 50 KM ---
    if settings.EVENTBRITE_TOKEN and lat and lon:
        try:
            url = "https://www.eventbriteapi.com/v3/events/search/"
            headers = {"Authorization": f"Bearer {settings.EVENTBRITE_TOKEN}"}
            params = {
                "location.latitude": lat,
                "location.longitude": lon,
                "location.within": "50km",
                "start_date.range_start": f"{data_str}T00:00:00Z",
                "start_date.range_end": f"{data_str}T23:59:59Z"
            }
            r = requests.get(url, headers=headers, params=params).json()

            for e in r.get("events", []):
                eventi.append({
                    "name": e.get("name", {}).get("text", "Senza titolo"),
                    "url": e.get("url", ""),
                    "classifications": [{"segment": {"name": "Eventbrite"}}],
                    "venue": e.get("venue_id", "Unknown")
                })

            print(f"     > Eventbrite: trovati {len(r.get('events', []))} eventi.")
        except Exception as e:
            print("     > Errore Eventbrite:", e)

    # --- 3️⃣ BANDSINTOWN (solo musica) ---
    if "musica" in [i.lower() for i in interessi_eventi] and lat and lon:
        try:
            url = "https://rest.bandsintown.com/events/"
            params = {
                "location": f"{lat},{lon}",
                "radius": 50,
                "date": data_str,
                "app_id": "roadtrip_app"
            }
            r = requests.get(url, params=params).json()

            if isinstance(r, list):
                for e in r:
                    eventi.append({
                        "name": e.get("title", "Concerto"),
                        "url": e.get("url", ""),
                        "classifications": [{"segment": {"name": "Music"}}],
                        "venue": e.get("venue", {}).get("name", "Unknown")
                    })

            print(f"     > Bandsintown: trovati {len(r) if isinstance(r, list) else 0} eventi.")
        except Exception as e:
            print("     > Errore Bandsintown:", e)

    # --- 4️⃣ RICERCA WEB (DuckDuckGo) ---
    eventi_web = cerca_eventi_web(citta, data, country_code, interessi_eventi)
    eventi.extend(eventi_web)

    # --- 5️⃣ FILTRO PER INTERESSI ---
    mappa = mappa_interessi_eventi(interessi_eventi)
    target_classifications = [c.lower() for c in mappa["classifications"]]
    target_keywords = [k.lower() for k in mappa["keywords"]]

    eventi_filtrati = []

    for e in eventi:
        nome = e["name"].lower()
        rilevante = False
        
        is_web = any(c.get("segment", {}).get("name") == "Evento dal Web" for c in e.get("classifications", []))
        if is_web:
            rilevante = True

        if not rilevante and any(k in nome for k in target_keywords):
            rilevante = True

        if not rilevante:
            for c in e.get("classifications", []):
                segment_name = c.get("segment", {}).get("name", "").lower()
                genre_name = c.get("genre", {}).get("name", "").lower()
                
                if any(tc in segment_name or tc in genre_name for tc in target_classifications):
                    rilevante = True
                    break

        if rilevante:
            eventi_filtrati.append(e)

    if not eventi_filtrati and eventi:
        eventi_filtrati = eventi

    print(f"     > Totale eventi filtrati per interessi (passati all'LLM): {len(eventi_filtrati)}")

    return eventi_filtrati
