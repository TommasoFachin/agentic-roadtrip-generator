import requests
import json

# --- ENDPOINTS ---
URL_CHATBOT = "http://127.0.0.1:8000/chatbot/messaggio"
URL_LLM = "http://127.0.0.1:8000/interpreta-richiesta"
URL_PLANNER = "http://127.0.0.1:8000/genera-itinerario"


# ============================================================
# STEP A — CHATBOT INTERATTIVO (profilo utente + TinyDB)
# ============================================================

print("\n=== CHATBOT PROFILO UTENTE ===")
print("Scrivi i tuoi messaggi. Scrivi 'fine' per terminare la chat.\n")

while True:
    testo = input("Tu: ")

    if testo.lower().strip() == "fine":
        print("\nChatbot terminato. Passo allo STEP B...\n")
        break

    payload = {"messaggio": testo}
    response = requests.post(URL_CHATBOT, json=payload)

    print("\nSTATUS:", response.status_code)
    try:
        print("RISPOSTA CHATBOT:")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except:
        print("Risposta non JSON:", response.text)

    print("\n----------------------------------------\n")


# ============================================================
# STEP B — TEST LLM (testo naturale → JSON viaggio)
# ============================================================

print("\n=== STEP B: Test LLM Viaggio ===")

testo = {
    "testo": "Vorrei un viaggio da Modena ad Amsterdam dal 1 al 5 maggio, massimo 400 km al giorno, interessato a arte e natura."
}

response_llm = requests.post(URL_LLM, json=testo)

print("STATUS:", response_llm.status_code)
print("JSON generato dall'LLM:")
print(json.dumps(response_llm.json(), indent=4, ensure_ascii=False))

json_viaggio = response_llm.json()


# ============================================================
# STEP C — TEST PLANNER (JSON → itinerario)
# ============================================================

print("\n=== STEP C: Test Planner ===")

response_planner = requests.post(URL_PLANNER, json=json_viaggio)

print("STATUS:", response_planner.status_code)
print("RISPOSTA PLANNER:")
try:
    print(json.dumps(response_planner.json(), indent=4, ensure_ascii=False))
except:
    print(response_planner.text)
