import os
import requests
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel

# Carica .env
load_dotenv()

model_name = os.getenv("OPENAI_MODEL")

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY non trovato nel .env")

# Modello Groq tramite OpenAI 
llm = OpenAIResponsesModel(
    model_name=model_name
)


# FUNZIONE METEO (SENZA TOOL CALLING)

def get_weather(city: str) -> str:
    city = city.strip()

    #Ottieni coordinate della città
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "it", "format": "json"}
    geo_resp = requests.get(geo_url, params=geo_params).json()

    if "results" not in geo_resp or not geo_resp["results"]:
        return f"La città '{city}' non esiste o non è stata trovata."

    lat = geo_resp["results"][0]["latitude"]
    lon = geo_resp["results"][0]["longitude"]

    # 2. Ottieni meteo attuale
    meteo_url = "https://api.open-meteo.com/v1/forecast"
    meteo_params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "timezone": "auto"
    }
    meteo_resp = requests.get(meteo_url, params=meteo_params).json()

    weather = meteo_resp["current_weather"]
    temp = weather["temperature"]
    wind = weather["windspeed"]
    code = weather["weathercode"]

    return f"A {city} ci sono {temp}°C, vento {wind} km/h, codice meteo {code}."

# AGENTE GROQ (SOLO PER ESTRARRE LA CITTÀ)
agent = Agent(
    model=llm,
    instructions=(
        "L'utente chiede il meteo. "
        "Estrai SOLO il nome della città dalla frase. "
        "Rispondi SOLO con il nome della città, senza altre parole."
    )
)


def chat_loop():
    print("\nAssistente meteo moderno attivo! Digita 'exit' per uscire.\n")

    while True:
        user_input = input("TU: ")
        if user_input.lower() == "exit":
            print("BOT: Alla prossima!")
            break

        # Il modello Groq estrae la città
        ai_response = agent.run_sync(user_input)
        city = ai_response.output.strip()

        weather = get_weather(city)

        print("BOT:", weather)

chat_loop()
