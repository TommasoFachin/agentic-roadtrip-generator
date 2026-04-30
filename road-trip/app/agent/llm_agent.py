from app.models import TripPreferences, TripPlan

def suggerisci_poi(preferenze: TripPreferences, partenza: str, destinazione: str):
    return [
        "Castello di esempio",
        "Parco naturale di esempio",
        "Centro storico di esempio"
    ]

def genera_documento_finale(itinerario: TripPlan) -> str:
    righe = [f"Itinerario di {len(itinerario.giorni)} giorni:"]
    for giorno in itinerario.giorni:
        righe.append(f"- Giorno {giorno.giorno} ({giorno.data}): {giorno.distanza_km} km, {giorno.durata_ore} ore")
    return "\n".join(righe)
