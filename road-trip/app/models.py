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

class TripPlan(BaseModel):
    giorni_totali: int
    stops: List[Stop]
