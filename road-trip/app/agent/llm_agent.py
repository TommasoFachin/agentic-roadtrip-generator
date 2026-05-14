import json
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from app.models import TripRequest

PROMPT = """
Sei un assistente che interpreta richieste di viaggio.
Rispondi SOLO con un JSON valido.
Non aggiungere testo prima o dopo.
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

    # 2) La tua versione usa SOLO str(result)
    raw_text = str(result)

    print("\n=== RISPOSTA RAW LLM ===")
    print(raw_text)

    # 3) Parsing JSON
    data = json.loads(raw_text)

    # 4) Validazione Pydantic
    return TripRequest(**data)
