import requests
import json

# 1) Endpoint LLM
URL_LLM = "http://127.0.0.1:8000/interpreta-richiesta"

# 2) Endpoint planner
URL_PLANNER = "http://127.0.0.1:8000/genera-itinerario"

# --- STEP 1: Testo naturale → JSON tramite LLM ---
testo = {
    "testo": "Vorrei un viaggio da Modena ad Amsterdam dal 1 al 5 maggio, massimo 400 km al giorno, interessato a arte e natura."
}

print("\n=== STEP 1: Chiamata all'LLM ===")
response_llm = requests.post(URL_LLM, json=testo)

print("STATUS:", response_llm.status_code)
print("JSON generato dall'LLM:")
print(json.dumps(response_llm.json(), indent=4, ensure_ascii=False))

# Salvo il JSON generato
json_viaggio = response_llm.json()

# --- STEP 2: JSON → Planner (/genera-itinerario) ---
print("\n=== STEP 2: Chiamata al planner ===")
response_planner = requests.post(URL_PLANNER, json=json_viaggio)

print("STATUS:", response_planner.status_code)
print("RISPOSTA:")
print(response_planner.text)

# Se la risposta è JSON, lo stampo formattato
try:
    print(json.dumps(response_planner.json(), indent=4, ensure_ascii=False))
except:
    pass
