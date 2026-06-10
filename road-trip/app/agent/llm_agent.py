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
from datetime import datetime

# ---------------------------------------------------------
# AGENTE 1 — INTERPRETAZIONE RICHIESTE DI VIAGGIO
# ---------------------------------------------------------

PROMPT_VIAGGIO = """
Sei un assistente che interpreta richieste di viaggio.

Devi restituire ESCLUSIVAMENTE un JSON valido che rispetta ESATTAMENTE questo schema:

{
  "luogo_partenza": "string",
  "luogo_destinazione": "string",
  "tappe_intermedie": [],
  "tappe_intermedie_utente": [],
  "data_partenza": "YYYY-MM-DD",
  "data_arrivo": "YYYY-MM-DD",
  "preferenze": {
    "distanza_massima_giornaliera": 0,
    "interessi_poi": ["string", "string"....ecc],
    "interessi_eventi": ["string", "string"....ecc]
  }
}

REGOLE IMPORTANTI:
- Usa SOLO questi campi, nessun altro.
- I nomi dei campi DEVONO essere identici.
- Non aggiungere testo fuori dal JSON.
- Non aggiungere commenti.
- Non aggiungere campi extra.
- ATTENZIONE ALLA CRONOLOGIA: Il testo che ricevi è la cronologia intera di una chat. DEVI dare la priorità assoluta agli ULTIMI MESSAGGI. Se l'utente ha cambiato destinazione, partenza, tappe o date nell'ultimo messaggio (es. ha cambiato idea da Copenaghen a Berlino), usa l'ultima richiesta e ignora quelle precedenti.
-Se l’utente indica esplicitamente una tappa intermedia (es: “voglio passare per Bolzano”, 
“fermati a Zurigo”, “tappa a Firenze”), inseriscila in tappe_intermedie_utente.

NON inventare tappe.
NON riempire tappe_intermedie_utente se l’utente non lo chiede chiaramente.

Le tappe_intermedie_utente rappresentano SOLO le tappe richieste dall’utente.
Le tappe_intermedie normali NON devono essere usate per il routing.

- IMPORTANTE: Per i luoghi di partenza e destinazione, inserisci sempre anche la Nazione per evitare ambiguità geografiche (es. "Modena, Italia", "Parigi, Francia").
- IMPORTANTE: Inserisci città in "tappe_intermedie" SOLO E SOLTANTO SE l'utente le ha esplicitamente richieste. ALTRIMENTI, DEVI lasciare l'array vuoto []. NON inventare mai tappe che l'utente non ha nominato!
- IMPORTANTE: Tieni conto della data di oggi per stabilire l'anno corretto se non viene specificato.
- IMPORTANTE: Traduci e restituisci gli "interessi_poi" e "interessi_eventi" SEMPRE IN ITALIANO (es. "città", "storia", "natura", "cibo").
- IMPORTANTE: Distingui chiaramente cosa visitare di giorno (interessi_poi come musei, piazze, natura) e cosa fare la sera (interessi_eventi come concerti, sport, festival).
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
    print("ERRORE CRITICO: IMPOSSIBILE AVVIARE L'APPLICAZIONE!")
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
Sei un assistente che aggiorna un profilo utente e risponde in modo naturale.

DEVI SEMPRE restituire un JSON con questa struttura:

{
  "aggiornamenti": {},
  "risposta": "testo naturale"
}

REGOLE:

1) "aggiornamenti" deve contenere SOLO le chiavi dei campi che sono stati modificati dall'ultimo messaggio.
IMPORTANTE: Quando modifichi un campo, devi restituire l'INTERA LISTA AGGIORNATA per quel campo (es. se rimuovi una tappa, restituisci la lista delle tappe rimanenti presa dal "Profilo attuale").
Usa SOLO queste chiavi per gli aggiornamenti:
   - interessi_poi (lista)
   - interessi_eventi (lista)
   - preferenze_viaggio (lista)
   - preferenze_cibo (lista)
   - tappe_obbligatorie (lista di stringhe con i nomi esatti delle città)
   - luogo_partenza (stringa)
   - luogo_destinazione (stringa)

2) Se l'utente chiede di RIMUOVERE un elemento (es. "togli Berlino"), rimuovilo dalla lista corrispondente del Profilo attuale e restituisci la nuova lista in "aggiornamenti".

3) Ignora saluti e frasi generiche. Se non ci sono informazioni utili usa "aggiornamenti": {}

4) "risposta" deve essere una frase naturale, amichevole e coerente con il messaggio e con gli "aggiornamenti" che hai fatto.

5) DISTINZIONE TAPPE:
   - La città dopo "da" è `luogo_partenza`.
   - La città dopo "a" o "fino a" è `luogo_destinazione`.
   - Le città dopo "tappa a", "passando per", "via" sono `tappe_obbligatorie`.
   - NON includere mai la destinazione finale o la partenza nella lista `tappe_obbligatorie`. Se sono già presenti, rimuovile esplicitamente.
   - Quando l'utente cambia idea su una destinazione o partenza, SOVRASCRIVI i vecchi valori e rimuovi le vecchie tappe non più rilevanti.

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

    # Diamo all'LLM la data di oggi per ancorarlo nel tempo reale
    oggi = datetime.now().strftime("%Y-%m-%d")
    testo_arricchito = f"DATA DI OGGI: {oggi}\nRICHIESTA UTENTE: {testo}"

    try:
        # Aggiunto timeout di 20 secondi
        result = await asyncio.wait_for(llm_viaggio.run(testo_arricchito), timeout=20.0)
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
Profilo attuale:
{json.dumps(profilo_attuale, ensure_ascii=False)}

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

PROMPT_POI_PRO = """
Sei un selezionatore professionale di punti di interesse (POI) per itinerari di viaggio.

Riceverai:
- gli interessi dell’utente
- una lista di POI trovati tramite OpenTripMap (che può essere incompleta)
- nome, categoria e rating di ogni POI

Il tuo compito è selezionare i MIGLIORI 5 POI, seguendo queste regole fondamentali:

────────────────────────────────────────
1) LANDMARK ICONICI (PRIORITÀ ASSOLUTA)
────────────────────────────────────────
Se la città è famosa, DEVI includere i suoi landmark iconici, ANCHE SE NON SONO PRESENTI nella lista fornita.

Esempi:
- Berlino → Muro di Berlino, Porta di Brandeburgo, Reichstag, East Side Gallery
- Parigi → Torre Eiffel, Louvre, Notre Dame, Arco di Trionfo
- Roma → Colosseo, Fontana di Trevi, Pantheon
- Londra → Big Ben, Tower Bridge, British Museum
- Praga → Ponte Carlo, Castello di Praga, Piazza della Città Vecchia
ecc.ecc.
Se mancano nella lista, AGGIUNGILI tu manualmente.

────────────────────────────────────────
2) COERENZA CON GLI INTERESSI
────────────────────────────────────────
Scegli POI che corrispondono agli interessi dell’utente.
Se l’utente ama:
- storia → monumenti, musei storici, siti archeologici
- natura → parchi, giardini, panorami
- architettura → edifici iconici, piazze, cattedrali
- arte → musei, gallerie, street art

────────────────────────────────────────
3) QUALITÀ E VARIETÀ
────────────────────────────────────────
- Preferisci POI con rating più alto.
- Evita POI troppo simili tra loro (es. 5 chiese).
- Preferisci POI famosi o significativi rispetto a POI minori.

────────────────────────────────────────
4) QUANDO LA LISTA È SCARSA
────────────────────────────────────────
Se i POI forniti sono pochi o irrilevanti:
- completa la lista con POI iconici della città
- aggiungi POI famosi usando la tua conoscenza generale

────────────────────────────────────────
5) OUTPUT
────────────────────────────────────────
Rispondi SOLO con JSON valido:

{
  "poi_selezionati": [
    {"nome": "Nome POI 1"},
    {"nome": "Nome POI 2"},
    {"nome": "Nome POI 3"},
    {"nome": "Nome POI 4"},
    {"nome": "Nome POI 5"}
  ]
}

NON aggiungere testo fuori dal JSON.
NON aggiungere commenti.
NON lasciare virgole finali.
"""

llm_poi = Agent(
    model=model,
    instructions=PROMPT_POI_PRO
)


# ---------------------------------------------------------
# AGENTE 4 — SELEZIONE EVENTI
# ---------------------------------------------------------

PROMPT_EVENTI = """
Sei un assistente che suggerisce eventi serali per un viaggiatore.

Riceverai:
- la città di destinazione per la serata
- gli interessi generali dell'utente (es. musica, sport, teatro)
- una lista di eventi disponibili per la serata con nome, tipo e luogo.

Il tuo compito è selezionare i MIGLIORI 2 eventi (massimo) che potrebbero piacere all'utente.

REGOLE DI SELEZIONE:
1. Scegli eventi pertinenti agli interessi dell'utente e che si svolgano EFFETTIVAMENTE nella città indicata o nelle immediate vicinanze.
2. SE UN EVENTO È LONTANO (es. in un'altra città) O È UN SITO SPAZZATURA/GENERICO (es. "Concerti in Italia", "Festival 2026", "Eventi TikTok"), DEVI SCARTARLO.
3. Se non ci sono eventi validi e locali, restituisci una lista vuota: {"eventi_selezionati": []}. È MEGLIO NON SUGGERIRE NULLA PIUTTOSTO CHE EVENTI LONTANI O FALSI.
4. Rispondi SOLO con un JSON valido, senza testo aggiuntivo.

STRUTTURA JSON DA RESTITUIRE:
{
  "eventi_selezionati": [
    {"nome": "Nome Evento 1"},
    {"nome": "Nome Evento 2"}
  ]
}
IMPORTANTE: Assicurati che il JSON sia formattato correttamente, senza virgole alla fine dell'ultimo elemento della lista.
"""

llm_eventi = Agent(
    model=model,
    instructions=PROMPT_EVENTI
)

async def seleziona_eventi_con_llm(lista_eventi: list, interessi_eventi: list, citta_tappa: str) -> list:
    if not lista_eventi:
        return []

    print("   > Analisi e selezione Eventi tramite LLM...")

    if not interessi_eventi:
        print("     Nessun interesse pertinente per gli eventi trovato nel profilo. Salto selezione.")
        return []

    # --- COMPRESSIONE EVENTI PER RISPARMIARE TOKEN ---
    eventi_compatti = []
    for e in lista_eventi[:15]:  # Limitiamo a 15 eventi per sicurezza
        class_list = e.get("classifications")
        classifications = class_list[0] if class_list else {}
        genere = classifications.get("genre", {}).get("name", "")
        segmento = classifications.get("segment", {}).get("name", "")
        tipo = f"{segmento} - {genere}".strip(" -") or "Evento"
        
        eventi_compatti.append({
            "nome": e.get("name"),
            "tipo": tipo,
            "luogo": e.get("venue", "Web / Sconosciuto")
        })

    prompt = f"""
Città della serata: {citta_tappa}

Interessi utente per gli eventi: {interessi_eventi}

Lista eventi disponibili:
{json.dumps(eventi_compatti, ensure_ascii=False)}

Seleziona i 2 migliori eventi secondo le regole.
SE NESSUN EVENTO È NELLA CITTÀ O VICINO, RESTITUISCI {{"eventi_selezionati": []}}.
Rispondi SOLO con JSON valido.
"""

    try:
        result = await asyncio.wait_for(llm_eventi.run(prompt), timeout=20.0)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        json_text = str(raw_output).strip()

        match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if not match: return []

        json_text = re.sub(r',\s*\]', ']', match.group(0))
        data = json.loads(json_text)
        return data.get("eventi_selezionati", [])
    except Exception as e:
        print(f"     Errore selezione Eventi: {e}")
        return []

async def seleziona_poi_con_llm(lista_poi: list, profilo: dict, citta_tappa: str) -> list:

    # Pre-filtro: ridotto a 40 per risparmiare Token. I monumenti famosi sono già in cima grazie al min_rate="3"!
    lista_poi = lista_poi[:100]

    poi_compatti = []

    for p in lista_poi:
        # --- CATEGORIA SEMPLIFICATA ---
        # 🔥 FIX ASSOLUTO: La chiave corretta è "kind", non "kinds"!
        kinds = p.get("kind", "")
        categoria = kinds.split(",")[0].replace("_", " ").capitalize() if kinds else "Varie"

        poi_compatti.append({
            "n": p.get("name"),
            "c": categoria,
            "r": float(p.get("rate", 0))
        })

    # FILTRO SALVAVITA: Rimuove i dati "sporchi" che confondono l'AI (es. "limite km: 250")
    interessi_raw = profilo.get("interessi_poi", [])
    interessi = [i for i in interessi_raw if "limite" not in i.lower() and "data" not in i.lower()]
    if not interessi:
        interessi = ["storia", "monumenti", "cultura", "luoghi iconici"]

    prompt = f"""
Città attuale: {citta_tappa}

Interessi utente per i luoghi da visitare: {interessi}

Lista POI disponibili (n=nome, c=categoria, r=rating):
{json.dumps(poi_compatti, ensure_ascii=False)}

IMPORTANTE:
- Aggiungi landmark iconici SOLO se la città è famosa (es. Berlino, Parigi, Roma, Londra, Tokyo).
- Se la città NON è famosa o non la riconosci, NON aggiungere landmark iconici inventati.
- Usa SOLO i POI presenti nella lista per le città non famose.
- Esempi per Berlino: Muro di Berlino, Porta di Brandeburgo, Reichstag, East Side Gallery, Museum Island.

Seleziona i 5 migliori POI secondo le regole.
Rispondi SOLO con JSON valido:
{{
  "poi_selezionati": [
    {{"nome": "..."}}
  ]
}}
"""



    try:
        result = await asyncio.wait_for(llm_poi.run(prompt), timeout=30.0)
        raw_output = getattr(result, 'data', getattr(result, 'output', ''))
        json_text = str(raw_output).strip()

        # Pulizia robusta in caso l'LLM aggiunga i backtick del Markdown
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
            
        json_text = json_text.strip()

        # --- ESTRAZIONE JSON ROBUSTA ---
        match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if not match:
            raise ValueError("Nessun JSON trovato nella risposta LLM")

        json_text = match.group(0)

        # --- FIX JSON: Rimuove le virgole finali (trailing commas) generate per errore dall'LLM ---
        json_text = re.sub(r',\s*\]', ']', json_text)
        json_text = re.sub(r',\s*\}', '}', json_text)

        data = json.loads(json_text)
        selezionati = data.get("poi_selezionati", [])

        poi_finali = []
        nomi_gia_aggiunti = set()
        for sel in selezionati:
            nome_poi = sel.get("nome")
            if not nome_poi or nome_poi in nomi_gia_aggiunti:
                continue

            # 1) Se il POI esiste in OpenTripMap → usa quello
            trovato = False
            for p in lista_poi:
                if p.get("name") == nome_poi:
                    poi_finali.append(p)
                    trovato = True
                    break

            # 2) Se NON esiste → aggiungi POI “virtuale” (landmark iconico)
            if not trovato:
                poi_finali.append({
                    "name": nome_poi,
                    "kind": "iconic",
                    "rate": 10,
                    "lat": None,
                    "lon": None
                })

            nomi_gia_aggiunti.add(nome_poi)
 

        # --- FIX SALVAVITA ---
        # Se l'LLM è stato pigro e ha restituito meno di 5 POI, riempiamo noi fino a 5
        if len(poi_finali) < 5:
            for p in lista_poi:
                if p not in poi_finali:
                    poi_finali.append(p)
                if len(poi_finali) == 5:
                    break
        return poi_finali[:5]

    except Exception as e:
        print(f"Errore selezione POI PRO: {e}")
        return lista_poi[:5]
