#questo file è il cervello matematico e logico del programma.


from datetime import datetime, timedelta, date
import asyncio
from app.models import TripPreferences, Stop, TripPlan, DayPlan
from fastapi import HTTPException
from app.services.poi_service import cerca_poi, mappa_interessi
import math
from app.services.event_service import cerca_eventi
import requests
from typing import List, Tuple
from app.services.geocoding_service import reverse_geocoding, geocoding_citta
from app.services.user_profile_service import get_user_profile
from app.agent.llm_agent import seleziona_poi_con_llm, seleziona_eventi_con_llm


class ItineraryNotPossibleError(Exception):
    """Eccezione sollevata quando l'itinerario non è fattibile con le specifiche fornite."""
    pass

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

        # se abbiamo raggiunto o superato la distanza massima → chiudiamo tappa
        if acc_km >= distanza_massima_giornaliera:
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
async def costruisci_itinerario(percorso: dict, preferenze, distanza_massima_giornaliera: float, data_partenza: date) -> TripPlan:
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

    tappe = costruisci_tappe_reali(percorso, distanza_massima_giornaliera)
    giorni_disponibili = len(tappe)

    ora_partenza_standard = datetime.strptime("09:00", "%H:%M")

    giorni = []
    tempo_extra = 0

    # 🔥 Applica il mapping degli interessi PRIMA di cercare i POI
    interessi_mappati = mappa_interessi(preferenze.interessi)
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

        # Punto di stop della tappa (fine giornata)
        lat_end, lon_end = tappa["end_coord"]

        # Città/paese della tappa
        print(f"   > Ricerca città di destinazione...")
        citta_tappa = reverse_geocoding(lat_end, lon_end)

        is_last_day = (i == len(tappe) - 1)
        poi_dict = {}
        poi_ordinati = []

        print(f"   > Ricerca POI su OpenTripMap...")
        if is_last_day:
            # ULTIMO GIORNO: Ricerca GRANDE e PULITA solo sulla destinazione finale.
            try:
                lon_f, lat_f = geocoding_citta(citta_tappa)
                
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

            if citta_tappa and citta_tappa != "Località sconosciuta":
                try:
                    lon_f, lat_f = geocoding_citta(citta_tappa)
                    risultati_finale = cerca_poi(lat=lat_f, lon=lon_f, kinds=kinds_base, radius=8000, limit=200)
                    for p in risultati_finale:
                        poi_dict[p["name"]] = p
                except:
                    pass
            
        # Ordina TUTTI i risultati per importanza (rate) decrescente
        poi_ordinati = sorted(poi_dict.values(), key=lambda x: -x.get("rate", 0))

        # --- SELEZIONE INTELLIGENTE DEI POI TRAMITE LLM ---
        print(f"   > Analisi e selezione POI tramite LLM (Mistral)... (potrebbe richiedere tempo)")
        poi = await seleziona_poi_con_llm(poi_ordinati, {"interessi": preferenze.interessi})

        # --- SELEZIONE EVENTI TRAMITE LLM ---
        # Usa gli interessi generali del profilo utente, non quelli del viaggio specifico
        lista_eventi = cerca_eventi(citta_tappa, giorno_data, profilo.interessi)
        eventi = await seleziona_eventi_con_llm(lista_eventi, profilo.interessi)
        
        # Pausa anti-spam per Groq: 12 secondi per permettere la ricarica dei token ed evitare l'errore 429
        await asyncio.sleep(12)
        print(f"   > Giorno {i + 1} completato con successo!")

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
            citta_tappa=citta_tappa
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
