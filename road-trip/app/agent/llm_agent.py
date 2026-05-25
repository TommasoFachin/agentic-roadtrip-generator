# modulo di AI. contiene la configurazione dell'agente pydanticAIe si collega 
# al modello Mistral tramite Ollama. L'agente è addestrato a interpretare richieste di
# viaggio in testo naturale e restituire un JSON strutturato secondo lo schema di TripRequest.

import json
import re
import asyncio
import os
from pathlib import Path
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from openai import AsyncOpenAI
from app.models import TripRequest

# ---------------------------------------------------------
# AGENTE 1 — INTERPRETAZIONE RICHIESTE DI VIAGGIO
# ---------------------------------------------------------

PROMPT_VIAGGIO = """
Sei un assistente che interpreta richieste di viaggio.

Devi restituire ESCLUSIVAMENTE un JSON valido che rispetta ESATTAMENTE questo schema:

{
  "luogo_partenza": "string",
  "luogo_destinazione": "string",
  "data_partenza": "YYYY-MM-DD",
  "data_arrivo": "YYYY-MM-DD",
  "preferenze": {
    "distanza_massima_giornaliera": 0,
    "interessi": ["string", "string"....ecc]
  }
}

REGOLE IMPORTANTI:
- Usa SOLO questi campi, nessun altro.
- I nomi dei campi DEVONO essere identici.
- Non aggiungere testo fuori dal JSON.
- Non aggiungere commenti.
- Non aggiungere campi extra.
- IMPORTANTE: Per i luoghi di partenza e destinazione, inserisci sempre anche la Nazione per evitare ambiguità geografiche (es. "Modena, Italia", "Parigi, Francia").
- IMPORTANTE: Traduci e restituisci gli "interessi" SEMPRE IN ITALIANO (es. "città", "storia", "natura", "cibo").
"""

# Forziamo le variabili globali in modo che PydanticAI usi Groq di default
# Leggiamo il file .env manualmente come file di testo per bypassare i bug di Windows
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
try:
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("GROQ_API_KEY"):
                chiave_groq = line.split("=", 1)[1].strip(" '\"\n")
                break
except FileNotFoundError:
    chiave_groq = None # Il file non esiste, la chiave è None

if not chiave_groq or not chiave_groq.startswith("gsk_"):
    print("\n" + "="*80)
    print("❌ ERRORE CRITICO: IMPOSSIBILE AVVIARE L'APPLICAZIONE!")
    print("La chiave API di Groq (GROQ_API_KEY) non è stata trovata o non è valida.")
    print(f"Percorso del file .env cercato: {env_path}")
    print("\nCONTROLLA QUESTI PUNTI:")
    print("1. Il file .env esiste in quella cartella?")
    print("2. Il file non si chiama '.env.txt' per errore?")
    print("3. Dentro al file, la riga è scritta ESATTAMENTE così: GROQ_API_KEY=gsk_tua_chiave_qui")
    print("   (Nessuno spazio, nessuna virgoletta, la chiave inizia con 'gsk_')")
    print("="*80 + "\n")
    raise SystemExit("ERRORE: GROQ_API_KEY non configurata. Il server non può partire.")

os.environ["OPENAI_API_KEY"] = chiave_groq
os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"

model = OpenAIChatModel(
    model_name="llama-3.1-8b-instant"
)

llm_viaggio = Agent(
    model=model,
    instructions=PROMPT_VIAGGIO
)

# ---------------------------------------------------------
# AGENTE 2 — CHATBOT PROFILO UTENTE
# ---------------------------------------------------------

PROMPT_CHATBOT = """
Sei un assistente che aggiorna un profilo utente.

Il tuo compito è estrarre SOLO le informazioni utili dal messaggio dell’utente
e restituire SOLO un JSON con i campi da aggiornare.
La risposta naturale verrà generata dal sistema, NON da te.

REGOLE:

1) Ignora completamente saluti e frasi generiche:
   "ciao", "hey", "ok", "bene", "grazie", "come va", "buongiorno", ecc.
   Se il messaggio contiene SOLO questo → restituisci {}.

2) NON interpretare parole casuali come interessi.

3) Considera interessi SOLO se sono categorie reali:
   arte, natura, sport, musica, fotografia, storia, tecnologia,
   viaggi, cibo, cultura, architettura.

4) Campi validi che puoi restituire:
   - interessi (lista)
   - budget
   - stile_viaggio
   - preferenze_cibo
   - allergie
   - citta_preferite

5) Se non trovi informazioni utili → restituisci {}.

Rispondi SOLO con un JSON valido.
"""


llm_chatbot = Agent(
    model=model,
    instructions=PROMPT_CHATBOT
)


# ---------------------------------------------------------
# AGENTE 3 — RISPOSTA NATURALE (MODELLO VELOCE)
# ---------------------------------------------------------

PROMPT_RISPOSTA = """
Rispondi in modo molto breve, naturale e amichevole.
Massimo 1 frase.

Regole:
- Non fare spiegazioni lunghe.
- Non parlare di coscienza, pianeti, realtà, ecc.
- Non offrire servizi o capacità.
- Rispondi come in una chat normale tra persone.
- Se l'utente saluta, rispondi con un saluto breve.
- Se l'utente fa una domanda semplice, rispondi in modo semplice.
"""

# MODELLO VELOCE SOLO PER LE RISPOSTE
model_risposta = OpenAIChatModel(
    model_name="llama-3.1-8b-instant"
)

llm_risposta = Agent(
    model=model_risposta,
    instructions=PROMPT_RISPOSTA
)

async def genera_risposta_naturale(messaggio: str) -> str:
    print("   > Generazione risposta naturale LLM in corso...")
    try:
        # Aumentato timeout a 15 secondi per reti lente
        result = await asyncio.wait_for(llm_risposta.run(messaggio), timeout=15.0)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        risposta = str(raw_output).strip()

        if risposta.startswith("```"):
            risposta = risposta.strip("`").strip()

        return risposta
    except Exception as e:
        print(f"\nErrore risposta naturale: {type(e).__name__} - {e}")
        return "Ok, ho capito."
# ---------------------------------------------------------
# FUNZIONE: interpreta richieste di viaggio
# ---------------------------------------------------------

async def interpreta_richiesta(testo: str) -> TripRequest:
    print(">>> AGENTE VIAGGIO ATTIVO <<<")

    try:
        # Aggiunto timeout di 20 secondi
        result = await asyncio.wait_for(llm_viaggio.run(testo), timeout=20.0)
        # Estraiamo l'output reale gestendo retrocompatibilità (output vs data in pydantic_ai)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        json_text = str(raw_output).strip()

        print("\n=== RISPOSTA RAW LLM ===")
        print(json_text)

        # Pulizia robusta in caso l'LLM aggiunga i backtick del Markdown
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]

        json_text = json_text.strip()

        # Estrae forzatamente solo il blocco JSON per evitare errori di decodifica
        match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if match:
            json_text = match.group(0)

        data = json.loads(json_text)
        return TripRequest(**data)
    except asyncio.TimeoutError:
        raise ValueError("Errore: Timeout! Groq ha impiegato più di 20 secondi a rispondere.")
    except Exception as e:
        print(f"\nErrore nell'agente di viaggio: {type(e).__name__} - {e}")
        raise ValueError("Impossibile estrarre JSON dall'LLM") from e

# ---------------------------------------------------------
# FUNZIONE: interpreta messaggi del chatbot
# ---------------------------------------------------------

async def interpreta_messaggio_chatbot(messaggio: str, profilo_attuale: dict) -> dict:
    """
    L'LLM deve:
    - estrarre gli aggiornamenti del profilo (aggiornamenti)
    - generare una risposta naturale (risposta)
    Restituisce un dict con chiavi: "aggiornamenti", "risposta".
    """

    prompt = f"""
Sei un assistente che aggiorna un profilo utente e risponde in modo naturale.

DEVI SEMPRE restituire un JSON con questa struttura:

{{
  "aggiornamenti": {{}},
  "risposta": "testo naturale"
}}

REGOLE:

1) "aggiornamenti" deve contenere SOLO informazioni utili al profilo:
   - interessi (lista)
   - preferenze_viaggio (lista)
   - preferenze_cibo (lista)
   - tappe_obbligatorie

2) Ignora completamente saluti e frasi generiche:
   "ciao", "hey", "ok", "bene", "grazie", "come va", "buongiorno", ecc.
   Se il messaggio contiene SOLO questo → usa:
   "aggiornamenti": {{}}

3) NON interpretare parole casuali come interessi.
   Considera interessi SOLO se sono categorie reali:
   arte, natura, sport, musica, fotografia, storia, tecnologia,
   viaggi, cibo, cultura, architettura e altre.

4) "risposta" deve essere una frase naturale, amichevole e coerente con il messaggio.
   - Se il messaggio è un saluto → rispondi come in una chat normale.
   - Se il messaggio contiene preferenze → conferma che aggiorni il profilo.

5) Rispondi SEMPRE e SOLO con un JSON valido.
   Nessun testo fuori dal JSON.

Profilo attuale:
{profilo_attuale}

Messaggio dell'utente:
"{messaggio}"
"""

    print("   > Analisi messaggio Chatbot tramite LLM in corso...")
    try:
        # Aggiunto timeout di 15 secondi
        result = await asyncio.wait_for(llm_chatbot.run(prompt), timeout=15.0)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        json_text = str(raw_output).strip()

        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]

        json_text = json_text.strip()

        # Estrae forzatamente solo il blocco JSON per evitare errori di decodifica
        match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if match:
            json_text = match.group(0)

        data = json.loads(json_text)
        
        if not isinstance(data, dict):
            data = {}
            
        if "aggiornamenti" not in data or not isinstance(data["aggiornamenti"], dict):
            data["aggiornamenti"] = {}
        if "risposta" not in data:
            data["risposta"] = "Ok!"
        return data
    except asyncio.TimeoutError:
        print("\nErrore Chatbot LLM: Timeout! (Problema di rete o server Groq irraggiungibile)")
        return {"aggiornamenti": {}, "risposta": "Scusa, la mia connessione ad internet fa i capricci. Puoi ripetere?"}
    except Exception as e:
        print(f"\nErrore Chatbot LLM: {type(e).__name__} - {e}")
        return {"aggiornamenti": {}, "risposta": "Non ho capito bene, puoi ripetere?"}


# ---------------------------------------------------------
# FUNZIONE: selezione POI
# ---------------------------------------------------------

PROMPT_POI = """
Sei un estrattore di dati. Il tuo unico scopo è ricevere liste di luoghi e restituire un JSON.
NON SEI un assistente conversazionale.
NON DEVI MAI generare testo fuori dal JSON, nessuna spiegazione, nessun saluto, nessuna premessa.
"""
llm_poi = Agent(
    model=model,
    instructions=PROMPT_POI
)

async def seleziona_poi_con_llm(lista_poi: list, profilo: dict) -> list:
    if not lista_poi:
        return []

    # Ottimizzazione: inviamo all'LLM fino a 60 POI. 
    # Visto che usiamo Groq (molto veloce), l'LLM può analizzare più opzioni.
    poi_semplificati = [{"nome": p["name"], "categoria": p["kind"]} for p in lista_poi[:60]]
    interessi = profilo.get("interessi", [])

    prompt = f"""
Interessi dell'utente: {interessi}

Lista dei POI disponibili:
{json.dumps(poi_semplificati, ensure_ascii=False)}

Scegli ESATTAMENTE 5 POI coerenti con gli interessi dell'utente (se la lista ne contiene meno di 5, sceglili tutti).
Dai priorità assoluta ai luoghi più famosi e iconici (es. a Parigi la Torre Eiffel, a Berlino il Muro, ecc.), ma assicurati sempre di completare la lista fino a 5.
Rispondi RESTITUENDO ESCLUSIVAMENTE IL JSON con questa esatta struttura:
{{
  "nomi_poi_selezionati": ["nome 1", "nome 2", "nome 3", "nome 4", "nome 5"]
}}
"""

    try:
        # Abbassato il timeout a 30s: Mistral con input ridotto deve rispondere molto più in fretta
        result = await asyncio.wait_for(llm_poi.run(prompt), timeout=30.0)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        json_text = str(raw_output).strip()

        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]

        json_text = json_text.strip()

        # Estrae forzatamente solo il blocco JSON per evitare errori di decodifica
        match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if match:
            json_text = match.group(0)

        data = json.loads(json_text)
        
        if not isinstance(data, dict):
            return lista_poi[:3]
            
        # Otteniamo la lista dei nomi scelti dall'AI
        nomi_selezionati = data.get("nomi_poi_selezionati", [])
        
        # Recuperiamo i dati completi originali (con coordinate e distanze) facendo un match sui nomi
        poi_scelti_completi = [p for p in lista_poi if p["name"] in nomi_selezionati]
        
        return poi_scelti_completi if poi_scelti_completi else lista_poi[:3]
    except asyncio.TimeoutError:
        print("\nErrore nell'agente POI: Timeout! (Ollama ha impiegato più di 30 secondi per rispondere)")
        return lista_poi[:3]
    except Exception as e:
        print(f"\nErrore nell'agente POI: {type(e).__name__} - {e}")
        return lista_poi[:3]
