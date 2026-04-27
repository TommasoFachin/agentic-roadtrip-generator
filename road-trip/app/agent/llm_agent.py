from app.models import TripPreferences, TripPlan

def suggerisci_poi(preferenze: TripPreferences, partenza: str, destinazione: str):
    return [
        "Castello di esempio",
        "Parco naturale di esempio",
        "Centro storico di esempio"
    ]

def genera_documento_finale(itinerario: TripPlan) -> str:
    righe = [f"Itinerario di {itinerario.giorni_totali} giorni:"]
    for tappa in itinerario.stops:
        primo_poi = tappa.POI[0] if tappa.POI else "Nessun POI"
        righe.append(f"- {tappa.nome}: {primo_poi}")
    return "\n".join(righe)
