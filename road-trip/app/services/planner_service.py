#questo file è il cervello matematico e logico del programma.


from datetime import datetime, timedelta, date
import asyncio
from app.models import TripPreferences, Stop, TripPlan, DayPlan, TripRequest
from fastapi import HTTPException
from app.services.poi_service import cerca_poi, mappa_interessi
import math
from app.services.event_service import cerca_eventi
import requests
from typing import List, Tuple
from app.services.geocoding_service import reverse_geocoding, geocoding_citta
from app.services.user_profile_service import get_user_profile
from app.agent.llm_agent import seleziona_poi_con_llm, seleziona_eventi_con_llm
from app.config import settings
import aiohttp


class ItineraryNotPossibleError(Exception):
    """Eccezione sollevata quando l'itinerario non è fattibile con le specifiche fornite."""
    pass

async def cerca_immagine_citta(citta: str) -> str | None:
    """
    Cerca un'immagine reale della città usando:
    1) ricerca Wikipedia per trovare la pagina corretta
    2) estrazione dell'immagine principale della pagina
    3) filtro per evitare bandiere, stemmi, mappe, politici
    """

    # Ritardo di 1 secondo per non far scattare il blocco 429 di Wikipedia
    await asyncio.sleep(1)

    blacklist = ["flag", "coat of arms", "logo", "map", "politician", "parliament", "emblem", "seal", "symbol", "signature", "handshake", "summit", "collage"]
    headers = {
        "User-Agent": "RoadTripAcademicApp/1.0 (mailto:student@university.local)"
    }

    async with aiohttp.ClientSession(headers=headers) as session:

        # 1️⃣ CERCA LA PAGINA DELLA CITTÀ
        # Cerchiamo solo il nome della città per evitare che la nazione confonda Wikipedia EN
        search_term = citta.split(",")[0].strip()
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "format": "json",
            "srsearch": search_term
        }



        try:
            async with session.get(search_url, params=search_params) as resp:
                data = await resp.json()

            results = data.get("query", {}).get("search", [])
            if not results:
                return None

            # Prendi il titolo della pagina più rilevante
            title = results[0]["title"]

        except Exception as e:
            print(f"     [Wikipedia API] Errore ricerca pagina per {citta}: {e}")
            return None

        # 2️⃣ OTTIENI L'IMMAGINE PRINCIPALE DELLA PAGINA
        image_url = "https://en.wikipedia.org/w/api.php"
        image_params = {
            "action": "query",
            "prop": "pageimages",
            "format": "json",
            "piprop": "thumbnail",
            "pithumbsize": 600,
            "titles": title
        }

        try:
            async with session.get(image_url, params=image_params) as resp:
                data = await resp.json()

            pages = data.get("query", {}).get("pages", {})
            for _, page in pages.items():
                img = page.get("thumbnail", {}).get("source")
                if not img:
                    continue

                # 3️⃣ FILTRO ANTI-IMMAGINI SBAGLIATE
                if any(bad in img.lower() for bad in blacklist):
                    continue

                return img

        except Exception as e:
            print(f"     [Wikipedia API] Errore ricerca immagine per {title}: {e}")
            return None

    return None

async def cerca_immagine_poi_wikipedia(nome_poi: str) -> str | None:
    """
    Cerca un'immagine del POI usando Wikipedia EN.
    Robusta contro 403, HTML, risposte non JSON.
    """
    await asyncio.sleep(1)

    headers = {"User-Agent": "RoadTripAcademicApp/1.0 (mailto:student@university.local)"}

    # 1️⃣ CERCA IL TITOLO
    params_search = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srsearch": nome_poi,
        "srlimit": 1
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get("https://en.wikipedia.org/w/api.php", params=params_search) as resp:

                if resp.status != 200:
                    return None

                if "application/json" not in resp.headers.get("Content-Type", ""):
                    return None

                data = await resp.json()

            results = data.get("query", {}).get("search", [])
            if not results:
                return None

            titolo = results[0]["title"]

        except:
            return None

        # 2️⃣ OTTIENI UNA THUMBNAIL (FUNZIONA SEMPRE)
        params_image = {
            "action": "query",
            "prop": "pageimages",
            "format": "json",
            "piprop": "thumbnail",
            "pithumbsize": 800,
            "titles": titolo
        }

        try:
            async with session.get("https://en.wikipedia.org/w/api.php", params=params_image) as resp:

                if resp.status != 200:
                    return None

                if "application/json" not in resp.headers.get("Content-Type", ""):
                    return None

                data = await resp.json()

            pages = data.get("query", {}).get("pages", {})
            for _, page in pages.items():
                thumb = page.get("thumbnail", {}).get("source")
                if thumb:
                    return thumb

        except:
            return None

    return None


async def traduci_citta_in_inglese(nome: str) -> str:
    """
    Cerca il titolo corretto della città su Wikipedia EN.
    Ritorna SEMPRE un nome valido e NON crasha mai.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srsearch": nome
    }

    headers = {
        "User-Agent": "RoadTripAcademicApp/1.0 (mailto:student@university.local)"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, params=params) as resp:
                # Se Wikipedia risponde con HTML → NON fare json()
                if resp.status != 200:
                    print(f"[traduci_citta] Wikipedia 403/errore per '{nome}' → uso nome originale")
                    return nome

                content_type = resp.headers.get("Content-Type", "")
                if "application/json" not in content_type:
                    print(f"[traduci_citta] Risposta NON JSON per '{nome}' → uso nome originale")
                    return nome

                data = await resp.json()

            results = data.get("query", {}).get("search", [])
            if not results:
                return nome

            return results[0]["title"]

        except Exception as e:
            print(f"[traduci_citta] Errore per '{nome}': {e}")
            return nome



async def cerca_immagine_commons(citta: str) -> str | None:
    """
    Cerca un'immagine iconica della città su Wikimedia Commons.
    Robusta contro 403, HTML, rate limit.
    """
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{citta} skyline OR landmark OR city",
        "gsrlimit": 10,
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json"
    }

    headers = {
        "User-Agent": "RoadTripAcademicApp/1.0 (mailto:student@university.local)"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, params=params) as resp:

                if resp.status != 200:
                    return None

                if "application/json" not in resp.headers.get("Content-Type", ""):
                    return None

                data = await resp.json()

            pages = data.get("query", {}).get("pages", {})
            for _, page in pages.items():
                info = page.get("imageinfo", [])
                if info:
                    return info[0].get("url")

        except:
            return None

    return None





def get_poi_image(poi: dict) -> str | None:
    """
    Restituisce l'immagine del POI se disponibile da OpenTripMap.
    """
    if not poi:
        return None

    # OpenTripMap preview image
    if "preview" in poi and "source" in poi["preview"]:
        return poi["preview"]["source"]

    return None

def get_population(city_name):
    # GeoNames non capisce bene le virgole: usiamo solo il nome della città per la ricerca
    nome_pulito = city_name.split(",")[0].strip()
    url = "http://api.geonames.org/searchJSON"
    params = {
        "q": nome_pulito,
        "maxRows": 1,
        "username": settings.GEONAMES_USERNAME
    }
    r = requests.get(url, params=params)
    data = r.json()

    if "geonames" in data and len(data["geonames"]) > 0:
        return data["geonames"][0].get("population", 0)

    return 0


def trova_citta_piu_grande_vicina(lat, lon, min_pop=1000):
    url = "http://api.geonames.org/findNearbyPlaceNameJSON"
    params = {
        "lat": lat,
        "lng": lon,
        "radius": 30,
        "cities": "cities1000",
        "username": settings.GEONAMES_USERNAME
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        if "geonames" in data and len(data["geonames"]) > 0:
            # Cerchiamo la prima città nei risultati che supera DAVVERO la soglia
            for city in data["geonames"]:
                pop = int(city.get("population", 0))
                if pop >= min_pop:
                    nome_completo = city["name"]
                    if city.get("countryName"):
                        nome_completo += f", {city['countryName']}"
                    return nome_completo, float(city["lat"]), float(city["lng"])
            
            # Se nessuna supera la soglia, prendiamo almeno la più grande trovata in zona
            migliore_trovata = max(data["geonames"], key=lambda x: int(x.get("population", 0)))
            nome_completo = migliore_trovata["name"]
            if migliore_trovata.get("countryName"):
                nome_completo += f", {migliore_trovata['countryName']}"
            return nome_completo, float(migliore_trovata["lat"]), float(migliore_trovata["lng"])
    except Exception as e:
        print(f"     Errore GeoNames findNearby: {e}")

    return None

#funzione per calcolare la distanza geodesica tra 2 cordinate
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """
    Distanza geodesica approssimata in km tra due punti.
    """
    R = 6371.0
    from math import radians, sin, cos, asin, sqrt

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c

#funzione che divide il viaggio in tappe reali basate sulla distanza massima giornaliera, e costruisce un itinerario giorno per giorno con orari realistici, città di tappa e POI rilevanti lungo la tappa.
def costruisci_tappe_reali(percorso: dict, distanza_massima_giornaliera: float) -> List[dict]:
    """
    Divide il percorso reale (geometry) in tappe basate sulla distanza massima giornaliera.
    Ogni tappa ha:
      - distanza_km
      - durata_sec (proporzionale)
      - start_coord (lat, lon)
      - end_coord (lat, lon)
    """
    geometry = percorso.get("geometry")
    if not geometry or len(geometry) < 2:
        raise ItineraryNotPossibleError("Percorso non valido: geometria mancante o troppo corta.")

    distanza_totale_km = percorso["distanza_km"]
    durata_totale_sec = percorso["durata_sec"]
    way_points = percorso.get("way_points", [])
    
    # way_points contiene gli indici della partenza, tappe intermedie e arrivo.
    # Estraiamo solo gli indici delle tappe intermedie (escludendo start e end).
    tappe_obbligatorie_idx = set(way_points[1:-1]) if len(way_points) > 2 else set()

    # calcolo distanza di ogni segmento e lista cumulativa
    segmenti = []
    dist_tot_check = 0.0

    for i in range(len(geometry) - 1):
        lon1, lat1 = geometry[i]
        lon2, lat2 = geometry[i + 1]
        d_km = haversine_km(lat1, lon1, lat2, lon2)
        dist_tot_check += d_km
        segmenti.append({
            "start": (lat1, lon1),
            "end": (lat2, lon2),
            "distanza_km": d_km
        })

    # se la somma differisce molto dalla distanza_totale_km, usiamo comunque la proporzione
    fattore = distanza_totale_km / dist_tot_check if dist_tot_check > 0 else 1.0
    for s in segmenti:
        s["distanza_km"] *= fattore

    tappe = []
    acc_km = 0.0
    acc_sec = 0.0
    tappa_start = segmenti[0]["start"]

    for idx, seg in enumerate(segmenti):
        d_km = seg["distanza_km"]
        # durata proporzionale alla distanza
        d_sec = durata_totale_sec * (d_km / distanza_totale_km)

        acc_km += d_km
        acc_sec += d_sec

        # Il punto di arrivo di questo segmento corrisponde all'indice idx + 1 nella geometry
        punto_arrivo_idx = idx + 1
        is_tappa_obbligatoria = punto_arrivo_idx in tappe_obbligatorie_idx

        # se abbiamo raggiunto la distanza massima o siamo arrivati a una tappa intermedia (evitando micro-tappe < 10km)
        if acc_km >= distanza_massima_giornaliera or (is_tappa_obbligatoria and acc_km > 10):
            tappa_end = seg["end"]
            tappe.append({
                "distanza_km": acc_km,
                "durata_sec": acc_sec,
                "start_coord": tappa_start,
                "end_coord": tappa_end
            })
            # reset per tappa successiva
            acc_km = 0.0
            acc_sec = 0.0
            tappa_start = tappa_end

    # eventuale ultima tappa residua
    if acc_km > 0:
        tappa_end = segmenti[-1]["end"]
        tappe.append({
            "distanza_km": acc_km,
            "durata_sec": acc_sec,
            "start_coord": tappa_start,
            "end_coord": tappa_end
        })

    return tappe

# funzione che, dato un percorso con geometria, estrae punti a frazioni specifiche del percorso (es. 1/3, 2/3) per cercare POI lungo la tappa in modo più distribuito e realistico.
def punti_lungo_tappa(geometry, start_coord, end_coord, fractions=(1/3, 2/3, 1.0)):
    """
    Restituisce una lista di punti (lat, lon) lungo la tappa.
    Usa la polyline per trovare i punti più vicini alle frazioni richieste.
    """

    # Trova gli indici nella polyline più vicini a start e end
    def trova_indice_piu_vicino(lat, lon):
        best_idx = 0
        best_dist = float("inf")
        for i, (lon2, lat2) in enumerate(geometry):
            d = haversine_km(lat, lon, lat2, lon2)
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx

    start_idx = trova_indice_piu_vicino(*start_coord)
    end_idx = trova_indice_piu_vicino(*end_coord)

    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx

    segment = geometry[start_idx:end_idx + 1]

    # distanza cumulativa
    cumulative = [0.0]
    for i in range(1, len(segment)):
        lon1, lat1 = segment[i - 1]
        lon2, lat2 = segment[i]
        d = haversine_km(lat1, lon1, lat2, lon2)
        cumulative.append(cumulative[-1] + d)

    total = cumulative[-1]
    if total == 0:
        lon, lat = segment[-1]
        return [(lat, lon) for _ in fractions]

    target_distances = [total * f for f in fractions]
    points = []

    for td in target_distances:
        idx = 0
        while idx < len(cumulative) and cumulative[idx] < td:
            idx += 1
        if idx >= len(segment):
            lon, lat = segment[-1]
        else:
            lon, lat = segment[idx]
        points.append((lat, lon))

    return points

# funzione principale che costruisce l'itinerario giorno per giorno, con orari realistici, città di tappa e POI rilevanti lungo la tappa.
async def costruisci_itinerario(percorso: dict, richiesta: TripRequest) -> TripPlan:
    """
    Genera un itinerario giorno per giorno basato su:
      - tappe reali lungo il percorso (distanza massima giornaliera)
      - orari realistici (pause, limite 20:00)
      - città/paese della tappa
      - POI rilevanti lungo la tappa (ancorati a città reali)
    """
    profilo = get_user_profile()

    distanza_totale = percorso["distanza_km"]
    durata_totale_sec = percorso["durata_sec"]

    # Estrai i parametri dalla richiesta
    distanza_massima_giornaliera = richiesta.preferenze.distanza_massima_giornaliera
    data_partenza = richiesta.data_partenza

    tappe = costruisci_tappe_reali(percorso, distanza_massima_giornaliera)
    giorni_disponibili = len(tappe)

    ora_partenza_standard = datetime.strptime("09:00", "%H:%M")

    giorni = []
    tempo_extra = 0

    # 🔥 Applica il mapping degli interessi PRIMA di cercare i POI
    interessi_mappati = mappa_interessi(richiesta.preferenze.interessi_poi)
    kinds_base = interessi_mappati
    
    for i, tappa in enumerate(tappe):
        print(f"\n--- [Planner] Elaborazione Giorno {i + 1}/{giorni_disponibili} ---")
        giorno_data = data_partenza + timedelta(days=i)

        distanza_giornaliera = tappa["distanza_km"]
        durata_giornaliera_sec = tappa["durata_sec"]

        # Partenza reale (se il giorno precedente è sforato)
        ora_partenza = ora_partenza_standard + timedelta(seconds=tempo_extra)

        # Durata base del giorno
        durata = durata_giornaliera_sec

        pause = int(durata // 7200) * 900

        # Pausa pranzo se si supera mezzogiorno
        # Se l'arrivo previsto supera le ore 12:00, aggiunge 30 min di pausa pranzo
        arrivo_previsto = ora_partenza + timedelta(seconds=durata + pause)
        if arrivo_previsto.hour >= 12:
            pause += 1800

        # Calcolo arrivo
        ora_arrivo = ora_partenza + timedelta(seconds=durata + pause)

        # Limite massimo arrivo alle 20:00
        limite = ora_partenza.replace(hour=20, minute=0)
        if ora_arrivo > limite:
            tempo_extra = (ora_arrivo - limite).seconds
            ora_arrivo = limite
        else:
            tempo_extra = 0

        is_last_day = (i == len(tappe) - 1)

        if is_last_day:
            # ULTIMO GIORNO: Forza la destinazione originale richiesta dall'utente
            citta_tappa = richiesta.luogo_destinazione
            lon_f, lat_f = geocoding_citta(citta_tappa)
            # Per la ricerca eventi, ci serve il country_code
            _, country_code = reverse_geocoding(lat_f, lon_f)
        else:
            # GIORNI INTERMEDI: Logica esistente
            lat_end, lon_end = tappa["end_coord"]
            print(f"   > Ricerca città di destinazione...")
            citta_tappa, country_code = reverse_geocoding(lat_end, lon_end)

            # --- FILTRO: accetta solo città > 1.000 abitanti ---
            lat_f, lon_f = lat_end, lon_end
            pop = get_population(citta_tappa)

            if pop < 1000:
                result = trova_citta_piu_grande_vicina(lat_end, lon_end)
                if result:
                    alternativa, lat_alt, lon_alt = result
                    pop_alt = get_population(alternativa)
                    if alternativa != citta_tappa:
                        if pop_alt >= 1000:
                            print(f"   > {citta_tappa} ha solo {pop} ab. Sostituita con {alternativa} ({pop_alt} ab.).")
                        else:
                            print(f"   > {citta_tappa} ha {pop} ab. Sostituita con {alternativa} ({pop_alt} ab.), la più grande in zona.")
                    else:
                        print(f"   > {citta_tappa} ({pop} ab.) mantenuta: è la più grande nel raggio di 30 km.")
                    citta_tappa = alternativa
                    lat_f, lon_f = lat_alt, lon_alt # Aggiorniamo coordinate con la nuova città!
                else:
                    print(f"   > Nessuna città >1k trovata vicino a {citta_tappa}. Mantengo quella trovata.")

        poi_dict = {}
        poi_ordinati = []

        print(f"   > Ricerca POI su OpenTripMap...")
        if is_last_day:
            # ULTIMO GIORNO: Ricerca GRANDE e PULITA solo sulla destinazione finale.
            try:
                # 1. Cerchiamo prima solo attrazioni di FAMA MONDIALE (salta le chiesette locali)
                risultati_finale = cerca_poi(
                    lat=lat_f,
                    lon=lon_f,
                    kinds=kinds_base,
                    radius=15000,
                    limit=500,
                    min_rate="3"
                )
                
                # 2. Fallback: Se trova poco, si tratta di una città media (cerchiamo fama nazionale)
                if len(risultati_finale) < 10:
                    risultati_finale = cerca_poi(
                        lat=lat_f, lon=lon_f, kinds=kinds_base, radius=15000, limit=500, min_rate="2"
                    )
                    
                # 3. Fallback: Se non trova nulla, è un paesino (cerchiamo tutto)
                if len(risultati_finale) < 5:
                    risultati_finale = cerca_poi(
                        lat=lat_f, lon=lon_f, kinds=kinds_base, radius=15000, limit=500
                    )
                
                for p in risultati_finale:
                    poi_dict[p["name"]] = p
            except Exception as e:
                print(f"     Errore ricerca POI finali: {e}")
        else:
            # GIORNI INTERMEDI: Logica precedente con ricerca a metà tappa e nella città di arrivo.
            geometry = percorso["geometry"]
            lat_start, lon_start = tappa["start_coord"]
            punti = punti_lungo_tappa(geometry, (lat_start, lon_start), (lat_end, lon_end), fractions=(0.5,))
            
            for lat_p, lon_p in punti:
                risultati = cerca_poi(lat=lat_p, lon=lon_p, kinds=kinds_base, radius=8000, limit=200)
                for p in risultati:
                    poi_dict[p["name"]] = p

            if citta_tappa and citta_tappa != "In viaggio":
                try:
                    risultati_finale = cerca_poi(lat=lat_f, lon=lon_f, kinds=kinds_base, radius=8000, limit=200)
                    for p in risultati_finale:
                        poi_dict[p["name"]] = p
                except:
                    pass
            
        # Ordina TUTTI i risultati per importanza (rate) decrescente
        poi_ordinati = sorted(poi_dict.values(), key=lambda x: -x.get("rate", 0))

        # --- SELEZIONE INTELLIGENTE DEI POI TRAMITE LLM ---
        print(f"   > Analisi e selezione POI tramite LLM (Groq)... (potrebbe richiedere tempo)")
        poi = await seleziona_poi_con_llm(
            poi_ordinati,
            {"interessi_poi": richiesta.preferenze.interessi_poi},
            citta_tappa
        )

        # --- SELEZIONE EVENTI TRAMITE LLM ---
        # Usa gli interessi generali del profilo utente, non quelli del viaggio specifico
        lista_eventi = cerca_eventi(citta_tappa, country_code, giorno_data, profilo.interessi_eventi)
        eventi = await seleziona_eventi_con_llm(lista_eventi, profilo.interessi_eventi, citta_tappa)
        
        immagine_url = None

        # 1️⃣ PRIORITÀ: POI iconici → cerca sempre su Wikipedia EN
        for p in poi:
            nome_poi = p.get("name", "").strip()
            if not nome_poi:
                continue

            # Cerca SEMPRE, anche se è una sola parola
            immagine_url = await cerca_immagine_poi_wikipedia(nome_poi)
            if immagine_url:
                break

        # 2️⃣ PRIORITÀ: immagine del POI da OpenTripMap
        if not immagine_url:
            for p in poi:
                img = get_poi_image(p)
                if img:
                    immagine_url = img
                    break

        if not immagine_url and citta_tappa:
            nome_pulito = citta_tappa.split(",")[0].strip()
            nome_en = await traduci_citta_in_inglese(nome_pulito)
            immagine_url = await cerca_immagine_commons(nome_en)
        if not immagine_url:
            immagine_url = "https://upload.wikimedia.org/wikipedia/commons/a/a8/Tour_Eiffel_Wikimedia_Commons.jpg"




                
        # Pausa anti-spam per Groq: 16 secondi per permettere la ricarica dei token ed evitare l'errore 429 (Rate Limit)
        await asyncio.sleep(16)
        print(f"   > Giorno {i + 1} completato con successo!")
        print("   > POI scelti:", [p.get("name") for p in poi])
        print("   > Immagine scelta:", immagine_url)

        giorno = DayPlan(
            giorno=i + 1,
            data=giorno_data,
            distanza_km=round(distanza_giornaliera, 2),
            durata_ore=round((durata + pause) / 3600, 2),
            ora_partenza=ora_partenza.strftime("%H:%M"),
            ora_arrivo=ora_arrivo.strftime("%H:%M"),
            note="Orari realistici con pause e limite massimo alle 20:00.",
            poi=poi,
            eventi=eventi,
            citta_tappa=citta_tappa,
            immagine_url=immagine_url
        )

        giorni.append(giorno)

    return TripPlan(
        distanza_totale_km=round(distanza_totale, 2),
        durata_totale_ore=round(durata_totale_sec / 3600, 2),
        giorni=giorni
    )

#funzione che, dato la distanza totale e la distanza massima giornaliera, calcola il numero di giorni necessari per completare il viaggio, e verifica se è fattibile con i giorni disponibili.
def calcola_tappe(distanza_km: float, distanza_massima_giornaliera: int) -> dict:
    if distanza_km <= 0:
        return {"error": "Distanza non valida", "required_days": 0}

    if distanza_massima_giornaliera <= 0:
        return {"error": "distanza_massima_giornaliera non valida", "required_days": 0}

    required_days = math.ceil(distanza_km / distanza_massima_giornaliera)

    return {
        "total_distance_km": distanza_km,
        "distanza_massima_giornaliera": distanza_massima_giornaliera,
        "required_days": required_days
    }

# funzione che, dato il numero di giorni richiesti e i giorni disponibili, verifica se il viaggio è fattibile e restituisce un messaggio esplicativo.
def verifica_fattibilita_viaggio(required_days: int, giorni_disponibili: int) -> dict:
    if required_days <= giorni_disponibili:
        return {
            "fattibile": True,
            "motivo": "Il viaggio è compatibile con i giorni disponibili."
        }

    return {
        "fattibile": False,
        "motivo": (
            f"Il viaggio richiede {required_days} giorni, "
            f"ma l'utente ne ha solo {giorni_disponibili}."
        )
    }
