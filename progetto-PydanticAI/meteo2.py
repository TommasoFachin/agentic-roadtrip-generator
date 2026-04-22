import requests
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

# MODELLO LOCALE (MISTRAL)
model = OpenAIChatModel(
    model_name='mistral',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'), # Nota /v1
)


# FUNZIONE PER OTTENERE IL METEO
def get_weather(city: str) -> dict:
    """Chiama Open-Meteo e restituisce temperatura, vento."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 0,
        "longitude": 0,
        "current_weather": True
    }

    # Ottieni latitudine e longitudine della città
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "it"}

    geo_resp = requests.get(geo_url, params=geo_params).json()

    if "results" not in geo_resp:
        return {"error": f"Non ho trovato la città '{city}'."}

    lat = geo_resp["results"][0]["latitude"]
    lon = geo_resp["results"][0]["longitude"]

    params["latitude"] = lat
    params["longitude"] = lon

    meteo_resp = requests.get(url, params=params).json()

    if "current_weather" not in meteo_resp:
        return {"error": "Errore nel recupero dei dati meteo."}

    return meteo_resp["current_weather"]


# AGENTE METEO

agent = Agent(
    model=model,
    instructions=(
        "Se l’utente chiede il meteo, estrai il nome della città e rispondi "
        "in modo naturale. Se la città non è chiara, chiedi chiarimenti."
    )
)



# LOOP INTERATTIVO (CLI)
def main():
    print("Assistente meteo (Ollama + Mistral) attivo! Digita 'exit' per uscire.\n")

    while True:
        user_input = input("TU: ")

        if user_input.lower() == "exit":
            break

        # Estrai la città usando il modello
        extraction = agent.run_sync(
            f"Estrai SOLO il nome della città da questa frase: '{user_input}'. "
            "Se non è una città, rispondi 'NESSUNA'."
        )

        city = extraction.output.strip()

        if city == "NESSUNA":
            print("BOT: Per favore dimmi una città.")
            continue

        # Ottieni il meteo
        meteo = get_weather(city)

        if "error" in meteo:
            print(f"BOT: {meteo['error']}")
            continue

        temp = meteo["temperature"]
        wind = meteo["windspeed"]

        print(f"BOT: A {city} ci sono {temp}°C, vento {wind} km/h.\n")


if __name__ == "__main__":
    main()
