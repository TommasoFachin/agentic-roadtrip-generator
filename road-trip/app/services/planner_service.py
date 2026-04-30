from datetime import datetime, timedelta, date
from app.models import TripPreferences, Stop, TripPlan
from fastapi import HTTPException
import math

class ItineraryNotPossibleError(Exception):
    """Eccezione sollevata quando l'itinerario non è fattibile con le specifiche fornite."""
    pass


def costruisci_itinerario(dati_percorso: dict, preferenze: TripPreferences, giorni_disponibili: int) -> TripPlan:
    distanza_totale = dati_percorso["distanza_km"]
    distanza_massima = preferenze.distanza_massima_giornaliera

    #CONTROLLO DI FATTIBILITÀ
    distanza_massima_totale = distanza_massima * giorni_disponibili

    if distanza_totale > distanza_massima_totale:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Impossibile generare l'itinerario: "
                f"servirebbero almeno {distanza_totale / distanza_massima:.1f} giorni, "
                f"ma l'utente ne ha solo {giorni_disponibili}."
            )
        )

    # Se è fattibile, calcolo i giorni necessari (entro il limite)
    giorni_necessari = int(distanza_totale // distanza_massima) + 1

    tappe = []
    ora_corrente = datetime.now()

    for i in range(giorni_necessari):
        tappa = Stop(
            nome=f"Tappa {i+1}",
            ora_arrivo=ora_corrente,
            ora_partenza=ora_corrente + timedelta(hours=4),
            POI=[f"POI esempio {i+1}"],
            distanza_tappa_precedente=distanza_massima if i > 0 else 0.0
        )
        tappe.append(tappa)
        ora_corrente += timedelta(days=1)

    return TripPlan(
        giorni_totali=giorni_necessari,
        stops=tappe
    )

def calcola_tappe(distanza_km: float, distanza_massima_giornaliera: int) -> dict:
    """
    Calcola il numero di tappe necessarie in base alla distanza totale
    e alla distanza massima giornaliera fornita dall'utente.
    """
    if distanza_km <= 0:
        return {
            "error": "Distanza non valida",
            "required_days": 0
        }

    if distanza_massima_giornaliera <= 0:
        return {
            "error": "distanza_massima_giornaliera non valida",
            "required_days": 0
        }

    required_days = math.ceil(distanza_km / distanza_massima_giornaliera)

    return {
        "total_distance_km": distanza_km,
        "distanza_massima_giornaliera": distanza_massima_giornaliera,
        "required_days": required_days
    }

def verifica_fattibilita_viaggio(required_days: int, giorni_disponibili: int) -> dict:
    """
    Verifica se il viaggio è fattibile confrontando i giorni necessari
    con i giorni disponibili.
    """
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