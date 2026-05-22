# modulo di AI. contiene la configurazione dell'agente pydanticAIe si collega 
# al modello Mistral tramite Ollama. L'agente è addestrato a interpretare richieste di
# viaggio in testo naturale e restituire un JSON strutturato secondo lo schema di TripRequest.

import json
import re
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
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
"""

model = OpenAIChatModel(
    model_name="mistral",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
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
    model_name="mistral:latest",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)

llm_risposta = Agent(
    model=model_risposta,
    instructions=PROMPT_RISPOSTA
)

async def genera_risposta_naturale(messaggio: str) -> str:
    try:
        result = await llm_risposta.run(messaggio)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        risposta = str(raw_output).strip()

        if risposta.startswith("```"):
            risposta = risposta.strip("`").strip()

        return risposta
    except:
        return 
# ---------------------------------------------------------
# FUNZIONE: interpreta richieste di viaggio
# ---------------------------------------------------------

async def interpreta_richiesta(testo: str) -> TripRequest:
    print(">>> AGENTE VIAGGIO ATTIVO <<<")

    try:
        result = await llm_viaggio.run(testo)
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
        data = json.loads(json_text)
        return TripRequest(**data)
    except Exception as e:
        print(f"\nErrore nell'agente di viaggio: {e}")
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

    try:
        result = await llm_chatbot.run(prompt)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        json_text = str(raw_output).strip()

        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]

        json_text = json_text.strip()
        data = json.loads(json_text)
        
        if not isinstance(data, dict):
            data = {}
            
        if "aggiornamenti" not in data or not isinstance(data["aggiornamenti"], dict):
            data["aggiornamenti"] = {}
        if "risposta" not in data:
            data["risposta"] = "Ok!"
        return data
    except Exception as e:
        print(f"\nErrore Chatbot LLM: {e}")
        return {"aggiornamenti": {}, "risposta": "Non ho capito bene, puoi ripetere?"}


# ---------------------------------------------------------
# FUNZIONE: selezione POI
# ---------------------------------------------------------

async def seleziona_poi_con_llm(lista_poi: list, profilo: dict) -> list:
    prompt = f"""
Profilo utente:
{json.dumps(profilo, indent=2)}

Lista dei POI disponibili:
{json.dumps(lista_poi, indent=2)}

Scegli SOLO i POI coerenti con gli interessi dell'utente.
Rispondi con:
{{
  "poi_selezionati": [...]
}}
"""

    try:
        result = await llm_viaggio.run(prompt)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        json_text = str(raw_output).strip()

        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]

        json_text = json_text.strip()
        data = json.loads(json_text)
        
        if not isinstance(data, dict):
            return lista_poi[:3]
            
        return data.get("poi_selezionati", lista_poi[:3])
    except Exception as e:
        print(f"\nErrore nell'agente POI: {e}")
        return lista_poi[:3]
