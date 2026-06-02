from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

class TripPreferences(BaseModel):
    interessi_poi: List[str] = []
    interessi_eventi: List[str] = []
    distanza_massima_giornaliera: float

class TripRequest(BaseModel):
    luogo_partenza: str
    luogo_destinazione: str
    data_partenza: date
    data_arrivo: date
    preferenze: TripPreferences
    tappe_intermedie: Optional[List[str]] = []


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
    eventi: list | None = None
    citta_tappa: str | None = None
    immagine_url: str | None = None

    

class TripPlan(BaseModel):
    distanza_totale_km: float
    durata_totale_ore: float
    giorni: List[DayPlan]

class UserProfile(BaseModel):
    interessi_poi: list[str] = []
    interessi_eventi: list[str] = []
    preferenze_viaggio: list[str] = []
    preferenze_cibo: list[str] = []
    tappe_obbligatorie: list[str] = []