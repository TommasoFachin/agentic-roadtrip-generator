import os
from pathlib import Path

# --- CARICAMENTO SICURO DELLE CHIAVI ---
# Leggiamo il file .env manualmente per bypassare i bug di Windows/dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
ORS_API_KEY_VALUE = None
TICKETMASTER_API_KEY_VALUE = None
GEONAMES_USERNAME_VALUE = "demo"

try:
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("ORS_API_KEY"):
                ORS_API_KEY_VALUE = line.split("=", 1)[1].strip(" '\"\n")
            elif line.strip().startswith("TICKETMASTER_API_KEY"):
                TICKETMASTER_API_KEY_VALUE = line.split("=", 1)[1].strip(" '\"\n")
            elif line.strip().startswith("GEONAMES_USERNAME"):
                GEONAMES_USERNAME_VALUE = line.split("=", 1)[1].strip(" '\"\n")
except FileNotFoundError:
    pass # La variabile rimarrà None

if not ORS_API_KEY_VALUE:
    print("\n" + "="*80)
    print("⚠️ ATTENZIONE: ORS_API_KEY non trovata nel file .env.")
    print("Il calcolo del percorso potrebbe fallire o avere limiti molto stretti.")
    print(f"Percorso del file .env cercato: {env_path}")
    print("="*80 + "\n")


class Settings:
    project_name: str = "Road Trip API"

    ORS_API_KEY = ORS_API_KEY_VALUE
    TICKETMASTER_API_KEY = TICKETMASTER_API_KEY_VALUE
    GEONAMES_USERNAME = GEONAMES_USERNAME_VALUE

    # 🔥 AGGIUNTE NECESSARIE PER LA RICERCA EVENTI
    EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN", None)
    BANDSINTOWN_APP_ID = "roadtrip_app"


settings = Settings()
