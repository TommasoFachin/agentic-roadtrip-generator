from pydantic import BaseModel
from datetime import date, datetime
from typing import List

class TripPreferences(BaseModel):
    interessi: List[str]
    distanza_massima_giornaliera: float

class TripRequest(BaseModel):
    luogo_partenza: str
    luogo_destinazione: str
    data_partenza: date
    data_arrivo: date
    preferenze: TripPreferences

class Stop(BaseModel):
    nome: str
    ora_arrivo: datetime | None = None
    ora_partenza: datetime | None = None
    POI: List[str] | None = None
    distanza_tappa_precedente: float | None = None

class DayPlan(BaseModel):
    giorno: int
    data: date
    distanza_km: float
    durata_ore: float
    ora_partenza: str
    ora_arrivo: str
    note: str
    poi: list | None = None
    citta_tappa: str | None = None

    

class TripPlan(BaseModel):
    distanza_totale_km: float
    durata_totale_ore: float
    giorni: List[DayPlan]

