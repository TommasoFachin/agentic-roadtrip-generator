from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

#in questo file il flusso è DIRETTO: Input Utente -> Modello -> risposta MOdello

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
    temperature=0.2, # Imposta la creatività del modello (0.0 = preciso, 1.0+ = creativo)
)

#chiede la lingua preferita all'utente
user_lang = input("in quale lingua deve parlare il both ? ").strip().lower()
system_prompt = SystemMessage(content=f"rispondi sempre in {user_lang} e non in altre lingue.")


# Crea una conversazione con un messaggio umano
def chat_loop():
    print("Digita 'exit' per uscire dalla chat.")
    #saluto iniziale del both
    
    # Lista per mantenere la cronologia della conversazione
    chat_history = [system_prompt]
    
    saluto_request = HumanMessage(content="Saluta l'utente in modo amichevole e chiedi come posso aiutarlo oggi.")
    chat_history.append(saluto_request)
    saluto = chat.invoke(chat_history)
    chat_history.append(saluto)
    print("BOTH:", saluto.content + "\n")
    while True:
        user_input = input("TU: ")
        if user_input.lower() == "exit":
            print("Uscita dalla chat.")
            break
        try:
            chat_history.append(HumanMessage(content=user_input))   #memoorizza la domanda dell'utente per il contesto futuro
            response = chat.invoke(chat_history)
            chat_history.append(response) # Memorizza la risposta per il contesto futuro
            print("BOTH:", response.content + "\n")
        except Exception as e: # Gestione più generica degli errori
            print(f"\nSi è verificato un errore: {e}")
            print("Controlla che le tue API key e l'endpoint di Azure siano corretti.")


#avvia la chat
chat_loop()
