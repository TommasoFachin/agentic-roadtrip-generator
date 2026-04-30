from fastapi import FastAPI
from app.models import TripRequest, TripPlan
from app.agent.llm_agent import suggerisci_poi, genera_documento_finale
from app.services.geocoding_service import geocodifica_citta
from app.services.routing_service import calcola_percorso
from app.services.planner_service import (
    costruisci_itinerario,
    calcola_tappe,
    verifica_fattibilita_viaggio
)

app = FastAPI()

@app.post("/genera-itinerario")
def genera_itinerario(richiesta: TripRequest):

    # Geocoding: città → coordinate
    lon_start, lat_start = geocodifica_citta(richiesta.luogo_partenza)
    lon_end, lat_end = geocodifica_citta(richiesta.luogo_destinazione)

    # Routing: distanza reale + durata
    percorso = calcola_percorso(
        lon_start, lat_start,
        lon_end, lat_end
    )

    # STEP 3.1 — Calcolo tappe in base ai km/giorno
    distanza_massima = richiesta.preferenze.distanza_massima_giornaliera
    tappe_info = calcola_tappe(
        distanza_km=percorso["distanza_km"],
        distanza_massima_giornaliera=distanza_massima
    )

    # Calcolo giorni disponibili
    giorni_disponibili = (richiesta.data_arrivo - richiesta.data_partenza).days + 1

    # STEP 3.2 — Verifica fattibilità del viaggio
    verifica = verifica_fattibilita_viaggio(
        required_days=tappe_info["required_days"],
        giorni_disponibili=giorni_disponibili
    )

    # Se il viaggio NON è fattibile → ritorno errore strutturato
    if not verifica["fattibile"]:
        return {
            "errore": "Viaggio non fattibile",
            "dettagli": verifica,
            "tappe_info": tappe_info,
            
        }

    # Se è fattibile → costruisco l’itinerario
    itinerario: TripPlan = costruisci_itinerario(
        percorso,
        richiesta.preferenze,
        giorni_disponibili,
        richiesta.data_partenza
    )

    # Generazione documento finale (LLM) — FUTURO
    documento = genera_documento_finale(itinerario)

    return {
        "tappe_info": tappe_info,
        "verifica": verifica,
        "itinerario": itinerario,
        "documento": documento
    }
