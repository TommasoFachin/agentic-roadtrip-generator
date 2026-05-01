from datetime import datetime, timedelta, date
from app.models import TripPreferences, Stop, TripPlan, DayPlan
from fastapi import HTTPException
import math

class ItineraryNotPossibleError(Exception):
    """Eccezione sollevata quando l'itinerario non è fattibile con le specifiche fornite."""
    pass


def costruisci_itinerario(percorso: dict, preferenze, giorni_disponibili: int, data_partenza) -> TripPlan:
    """
   -- Genera un itinerario giorno per giorno con:
    - distanza totale
    - durata totale
    - suddivisione giornaliera
    - orari realistici (pause, limite 20:00, sforamenti)
    """

    distanza_totale = percorso["distanza_km"]
    durata_totale_sec = percorso["durata_sec"]

    # Suddivisione giornaliera
    distanza_giornaliera = distanza_totale / giorni_disponibili
    durata_giornaliera_sec = durata_totale_sec / giorni_disponibili

    # Orario di partenza standard
    ora_partenza_standard = datetime.strptime("09:00", "%H:%M")

    giorni = []
    tempo_extra = 0  # tempo che sfora e va aggiunto al giorno successivo

    for i in range(giorni_disponibili):
        giorno_data = data_partenza + timedelta(days=i)

        # Partenza reale (se il giorno precedente è sforato)
        ora_partenza = ora_partenza_standard + timedelta(seconds=tempo_extra)

        # Durata base del giorno
        durata = durata_giornaliera_sec

        # Pausa ogni 2 ore → 15 minuti
        pause = int(durata // 7200) * 900  # 7200 sec = 2h, 900 sec = 15 min

        # Pausa pranzo se si supera mezzogiorno
        arrivo_previsto = ora_partenza + timedelta(seconds=durata + pause)
        if arrivo_previsto.hour >= 12:
            pause += 1800  # 30 min

        # Calcolo arrivo
        ora_arrivo = ora_partenza + timedelta(seconds=durata + pause)

        # Limite massimo arrivo alle 20:00
        limite = ora_partenza.replace(hour=20, minute=0)
        if ora_arrivo > limite:
            tempo_extra = (ora_arrivo - limite).seconds
            ora_arrivo = limite
        else:
            tempo_extra = 0

        giorno = DayPlan(
            giorno=i + 1,
            data=giorno_data,
            distanza_km=round(distanza_giornaliera, 2),
            durata_ore=round((durata + pause) / 3600, 2),
            ora_partenza=ora_partenza.strftime("%H:%M"),
            ora_arrivo=ora_arrivo.strftime("%H:%M"),
            note="Orari realistici con pause e limite massimo alle 20:00."
        )

        giorni.append(giorno)

    return TripPlan(
        distanza_totale_km=round(distanza_totale, 2),
        durata_totale_ore=round(durata_totale_sec / 3600, 2),
        giorni=giorni
    )


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
