from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

# Carica variabili da file .env
load_dotenv()

# Legge le variabili per Azure OpenAI dal file .env
api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("OPENAI_API_VERSION", "2023-05-15") # Versione di default

# Inizializza il modello Azure OpenAI
chat = AzureChatOpenAI(
    azure_deployment="gpt4o",
    api_version=api_version,
    azure_endpoint=azure_endpoint,
    api_key=api_key,
)

# Crea una conversazione con un messaggio umano
user_input = input("Dimmi tutto: ")
try:
    response = chat.invoke([HumanMessage(content=user_input)])
    print("dopo averci pensato:", response.content)
except Exception as e: # Gestione più generica degli errori
    print(f"\nSi è verificato un errore: {e}")
    print("Controlla che le tue API key e l'endpoint di Azure siano corretti.")
