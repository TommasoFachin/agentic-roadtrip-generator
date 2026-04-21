import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel

# Carica variabili .env
load_dotenv()

model_name = os.getenv("OPENAI_MODEL")

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY non trovato nel .env")

# Configurazione modello Groq tramite OpenAI shim
llm = OpenAIResponsesModel(
    model_name=model_name
)

# Lingua scelta dall'utente
user_lang = input("In quale lingua deve parlare il bot? ").strip().lower()

# Crea agente
agent = Agent(
    model=llm,
    instructions=f"Sei un assistente utile e amichevole. Rispondi sempre in {user_lang}."
)

def chat_loop():
    print("\nInizia la chat con il bot! Digita 'exit' per uscire.\n")

    # Primo messaggio
    greeting = agent.run_sync(
        "Saluta l'utente in modo amichevole e chiedi come puoi aiutarlo."
    )

    print("BOT:", greeting.output)

    # Loop conversazione
    while True:
        user_input = input("TU: ")
        if user_input.lower() == "exit":
            print("BOT: Alla prossima!")
            break

        response = agent.run_sync(user_input)

        print("BOT:", response.output)

chat_loop()
