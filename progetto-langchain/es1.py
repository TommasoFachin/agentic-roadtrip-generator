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
    temperature=0.4, # Imposta la creatività del modello (0.0 = preciso, 1.0+ = creativo)
)



# Crea una conversazione con un messaggio umano
def chat_loop():
    print("Digita 'exit' per uscire dalla chat.")
    #saluto iniziale del both
    saluto = chat.invoke([HumanMessage(content="Saluta l'utente in modo amichevole e chiedi come posso aiutarlo oggi.")])
    print("BOTH:", saluto.content + "\n")
    while True:
        user_input = input("TU: ")
        if user_input.lower() == "exit":
            print("Uscita dalla chat.")
            break
        try:
            response = chat.invoke([HumanMessage(content=user_input)])
            print("BOTH:", response.content + "\n")
        except Exception as e: # Gestione più generica degli errori
            print(f"\nSi è verificato un errore: {e}")
            print("Controlla che le tue API key e l'endpoint di Azure siano corretti.")


#avvia la chat
chat_loop()
