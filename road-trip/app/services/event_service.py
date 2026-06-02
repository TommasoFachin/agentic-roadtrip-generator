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
    """Cerca eventi su Ticketmaster per una data città e data, basandosi sugli interessi."""

    print(f"   > Ricerca eventi per {citta} il {data}...")

    start_date = datetime.combine(data, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date = datetime.combine(data, datetime.max.time()).strftime('%Y-%m-%dT%H:%M:%SZ')

    dati_ricerca = mappa_interessi_eventi(interessi_eventi)
    classifications = dati_ricerca["classifications"]
    keywords = dati_ricerca["keywords"]
    
    eventi_trovati = []

    if not settings.TICKETMASTER_API_KEY:
        print("   > ATTENZIONE: TICKETMASTER_API_KEY non configurata. Salto ricerca Ticketmaster.")
    else:
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
        if keywords:
            params["keyword"] = " ".join(keywords)

        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        try:
            response = requests.get(url, params=params, timeout=10)
            response_data = response.json()
            eventi_tm = response_data.get("_embedded", {}).get("events", [])
            eventi_trovati.extend(eventi_tm)
            
            log_msg = f"     Trovati {len(eventi_tm)} eventi su Ticketmaster."
            print(log_msg)
        except Exception as e:
            print(f"     Eccezione durante la chiamata a Ticketmaster: {e}")

    # INTEGRAZIONE RICERCA WEB
    # Aggiungiamo i risultati della ricerca web personalizzati in base agli interessi
    if citta != "In viaggio":
        eventi_web = cerca_eventi_web(citta, data, country_code, interessi_eventi)
        eventi_trovati.extend(eventi_web)

    return eventi_trovati