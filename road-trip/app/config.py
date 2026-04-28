from dotenv import load_dotenv
import os

# Carica il file .env
load_dotenv()



class Settings:
    project_name: str = "Road Trip API"
    # Potrai aggiungere qui le tue configurazioni future (es. openai_api_key)
    ORS_API_KEY = os.getenv("ORS_API_KEY")
settings = Settings()
