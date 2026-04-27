from fastapi import FastAPI
from app.models import TripRequest, TripPlan
from app.agent.llm_agent import suggerisci_poi, genera_documento_finale
from app.services.routing_service import calcola_percorso
from app.services.planner_service import costruisci_itinerario

app = FastAPI()

@app.post("/genera-itinerario")
def genera_itinerario(richiesta: TripRequest):
    poi = suggerisci_poi(
        richiesta.preferenze,
        richiesta.luogo_partenza,
        richiesta.luogo_destinazione
    )

    # geocoding → convertire indirizzi in coordinate
    percorso = calcola_percorso((44.65, 10.92), (45.15, 10.79))

    # Calcolo dei giorni disponibili
    giorni_disponibili = (richiesta.data_arrivo - richiesta.data_partenza).days + 1

    # Chiamata corretta
    itinerario: TripPlan = costruisci_itinerario(
        percorso,
        richiesta.preferenze,
        giorni_disponibili
    )

    documento = genera_documento_finale(itinerario)

    return {
        "itinerario": itinerario,
        "documento": documento
    }
