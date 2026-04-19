from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import os
import requests

# Carica variabili da file .env
load_dotenv()

# Legge le variabili per Azure OpenAI dal file .env
api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("OPENAI_API_VERSION", "2023-05-15")

# Inizializza il modello Azure OpenAI
chat = AzureChatOpenAI(
    azure_deployment="gpt4o",
    api_version=api_version,
    azure_endpoint=azure_endpoint,
    api_key=api_key,
    temperature=0.2, 
)

# Chiede la lingua preferita all'utente
user_lang = input("In quale lingua deve parlare il bot? ").strip().lower()

@tool
def ottieni_meteo(citta: str) -> str:
    """Utile per ottenere il meteo attuale di una città specificata."""
    try:
        risposta = requests.get(f"https://wttr.in/{citta}?format=3")
        risposta.raise_for_status()
        return risposta.text
    except Exception as e:
        return f"Errore nel recupero del meteo per {citta}: {e}"

tools = [ottieni_meteo]

# Creazione del prompt template per l'agente
prompt = ChatPromptTemplate.from_messages([
    ("system", f"Sei un assistente utile. Rispondi sempre in {user_lang} e non in altre lingue."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Creazione dell'agente e del suo esecutore
agent = create_tool_calling_agent(chat, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True) # verbose=True per vedere i ragionamenti

def chat_loop():
    print("Digita 'exit' per uscire dalla chat.")
    chat_history = []
    
    # Saluto iniziale
    print("BOT: Ciao! Sono il tuo assistente. Come posso aiutarti oggi?\n")
    
    while True:
        user_input = input("TU: ")
        if user_input.lower() == "exit":
            print("Uscita dalla chat.")
            break
        try:
            response = agent_executor.invoke({"input": user_input, "chat_history": chat_history})
            chat_history.extend([HumanMessage(content=user_input), AIMessage(content=response["output"])])
            print("BOT:", response["output"] + "\n")
        except Exception as e:
            print(f"\nSi è verificato un errore: {e}")

# Avvia la chat
chat_loop()