import requests
import json

URL = "http://127.0.0.1:8000/genera-itinerario"

# Carica il JSON della richiesta
with open("richiesta_viaggio.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

# Invia la richiesta POST
response = requests.post(URL, json=payload)

# Stampa il risultato
print("STATUS:", response.status_code)
print("RISPOSTA:")
print(response.text)

print(json.dumps(response.json(), indent=4, ensure_ascii=False))
