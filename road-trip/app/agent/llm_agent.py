import json
import re
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from app.models import TripRequest

PROMPT = """
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

llm_agent = Agent(
    model=model,
    instructions=PROMPT
)

async def interpreta_richiesta(testo: str) -> TripRequest:
    # 1) Chiamata all’LLM
    result = await llm_agent.run(testo)

    # 2) Convertiamo in stringa
    raw = str(result)

    print("\n=== RISPOSTA RAW LLM ===")
    print(raw)

    # 3) Estraiamo SOLO il JSON usando regex
    match = re.search(r"output='(.*)'", raw, re.DOTALL)
    if not match:
        raise ValueError("Impossibile estrarre JSON dall'LLM")

    json_text = match.group(1)

    # 4) Rimuoviamo eventuali escape
    json_text = json_text.replace("\\n", "\n").replace("\\'", "'")

    print("\n=== JSON ESTRATTO ===")
    print(json_text)

    # 5) Parsing JSON
    data = json.loads(json_text)

    # 6) Validazione Pydantic
    return TripRequest(**data)
