from fastapi import FastAPI
from app.models import TripRequest, TripPlan
from app.agent.llm_agent import suggerisci_poi, genera_documento_finale
from app.services.geocoding_service import geocodifica_citta
from app.services.routing_service import calcola_percorso
from app.services.planner_service import costruisci_itinerario

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

    # Calcolo giorni disponibili
    giorni_disponibili = (richiesta.data_arrivo - richiesta.data_partenza).days + 1

    # Pianificazione tappe
    itinerario: TripPlan = costruisci_itinerario(
        percorso,
        richiesta.preferenze,
        giorni_disponibili
    )

    # Generazione documento finale (LLM) SERVITà IN FUTURO
    #documento = genera_documento_finale(itinerario)

    return {
        "itinerario": itinerario,
        #"documento": documento IN FURTURO
    }
