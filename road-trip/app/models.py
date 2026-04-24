from pydantic import BaseModel
from datetime import date, datetime
from typing import List

class TripPreferences(BaseModel):
    interessi: List[str]
    distanza_max_giornaliera: float

class TripRequest(BaseModel):
    luogo_partenza: str
    luogo_destinazione: str
    data_partenza: date
    data_arrivo: date
    prefernze: TripPreferences

class Stop(BaseModel):
    nome: str
    ora_arrivo: datetime
    ora_partenza: datetime
    POI: List[str]
    distanza_tappa_precedente: float

class TripPlan(BaseModel):
    giorni_totali: int
    stops: List[Stop]
