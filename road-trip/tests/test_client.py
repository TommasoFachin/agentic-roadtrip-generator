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
print("TIP: Durante la chat, ricordati di specificare tutto il necessario:")
print("   - Luogo di partenza e destinazione")
print("   - Date (es. dal 1 al 5 maggio)")
print("   - Limite di km giornalieri\n")

storia_messaggi = []
dati_completi = False

while not dati_completi:
    while True:
        testo = input("Tu: ")

        if testo.lower().strip() == "fine":
            print("\nChatbot terminato. Passo allo STEP B (Verifica Dati)...\n")
            break

        storia_messaggi.append(testo)

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

    # Uniamo tutti i messaggi della chat in un unico grande testo di contesto
    testo_completo_chat = " ".join(storia_messaggi)

    if not testo_completo_chat.strip():
        print("ERRORE: Non hai scritto niente!")
        print("Inserisci i dati del viaggio prima di scrivere 'fine'.\n")
        continue

    testo = {
        "testo": testo_completo_chat
    }

    response_llm = requests.post(URL_LLM, json=testo)

    if response_llm.status_code == 200:
        print("Tutti i dati sono stati inseriti correttamente!")
        print("STATUS:", response_llm.status_code)
        print("JSON generato dall'LLM:")
        print(json.dumps(response_llm.json(), indent=4, ensure_ascii=False))
        
        json_viaggio = response_llm.json()
        dati_completi = True
    else:
        print("ERRORE: Dati del viaggio mancanti o non chiari.")
        print("L'intelligenza artificiale non ha trovato tutti i parametri obbligatori.")
        print("Assicurati di aver indicato: Luogo di partenza, Destinazione, Date (inizio e fine) e Max km/giorno.")
        print("Scrivi i dati mancanti qui sotto e digita di nuovo 'fine' per riprovare.\n")


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
