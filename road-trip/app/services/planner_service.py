from datetime import datetime, timedelta, date
from app.models import TripPreferences, Stop, TripPlan, DayPlan
from fastapi import HTTPException
import math

class ItineraryNotPossibleError(Exception):
    """Eccezione sollevata quando l'itinerario non è fattibile con le specifiche fornite."""
    pass


def costruisci_itinerario(percorso: dict, preferenze, giorni_disponibili: int, data_partenza) -> TripPlan:
    """
    STEP 3.3 — Genera un itinerario giorno per giorno basato su:
    - distanza totale del percorso
    - durata totale del percorso
    - giorni disponibili
    - suddivisione realistica delle tappe
    """

    distanza_totale = percorso["distanza_km"]
    durata_totale_sec = percorso["durata_sec"]

    # Suddivisione giornaliera
    distanza_giornaliera = distanza_totale / giorni_disponibili
    durata_giornaliera_sec = durata_totale_sec / giorni_disponibili

    # Orario di partenza standard
    ora_partenza = datetime.strptime("09:00", "%H:%M")

    giorni = []

    for i in range(giorni_disponibili):
        # Data del giorno i-esimo
        giorno_data = data_partenza + timedelta(days=i)

        # Orario di arrivo stimato
        ora_arrivo = ora_partenza + timedelta(seconds=durata_giornaliera_sec)

        giorno = DayPlan(
            giorno=i + 1,
            data=giorno_data,
            distanza_km=round(distanza_giornaliera, 2),
            durata_ore=round(durata_giornaliera_sec / 3600, 2),
            ora_partenza=ora_partenza.strftime("%H:%M"),
            ora_arrivo=ora_arrivo.strftime("%H:%M"),
            note="Tappa generata automaticamente in base alla distanza totale e ai giorni disponibili."
        )

        giorni.append(giorno)

    return TripPlan(
        distanza_totale_km=round(distanza_totale, 2),
        durata_totale_ore=round(durata_totale_sec / 3600, 2),
        giorni=giorni
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