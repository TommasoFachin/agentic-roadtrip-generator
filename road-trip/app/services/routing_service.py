import requests
from app.config import settings

#def get_route(luogo_partenza: str, luogo_destinazione: str) -> dict:
    # qui in futuro OpenRouteService o simili
    # Per ora simulo una risposta
 #   return {
  #      "distanza_km": 800.0,
   #     "durata_min": 480.0
   # }

def calcola_percorso(luogo_partenza: str, luogo_destinazione: str):
    return {
        "partenza": luogo_partenza,
        "destinazione": luogo_destinazione,
        "distanza_km": 800.0,
        "durata_min": 480.0
    }   
