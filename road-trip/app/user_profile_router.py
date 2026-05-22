from fastapi import APIRouter
from pydantic import BaseModel
from app.services.user_profile_service import get_user_profile, update_user_profile
from app.agent.llm_agent import interpreta_messaggio_chatbot
from app.agent.llm_agent import genera_risposta_naturale

router = APIRouter(prefix="/chatbot", tags=["Chatbot Profilo Utente"])

# modello per ricevere messaggi dal chatbot
class ChatbotMessage(BaseModel):
    messaggio: str


# -------------------------------
# FUNZIONE DI NORMALIZZAZIONE
# -------------------------------
def _normalizza_aggiornamenti(agg):
    """
    Converte campi annidati come:
    {
      "preferenze": {
         "interessi": [...],
         "stile_viaggio": "economico"
      }
    }
    in:
    {
      "interessi": [...],
      "stile_viaggio": "economico"
    }
    """
    normalizzato = {}

    for key, value in agg.items():
        if key == "preferenze" and isinstance(value, dict):
            for subkey, subvalue in value.items():
                normalizzato[subkey] = subvalue
        else:
            normalizzato[key] = value

    return normalizzato


# -------------------------------
# ENDPOINT CHATBOT
# -------------------------------
@router.post("/messaggio")
async def chatbot_messaggio(payload: ChatbotMessage):
    messaggio = payload.messaggio.strip()

    profilo = get_user_profile()

    # Convertiamo in dizionario così l'LLM vedrà un JSON reale invece di un oggetto Pydantic
    # 1) estrai aggiornamenti del profilo
    risultato = await interpreta_messaggio_chatbot(messaggio, profilo.model_dump())
    aggiornamenti = risultato.get("aggiornamenti", {})

    # 2) genera risposta naturale con agente dedicato
    risposta = await genera_risposta_naturale(messaggio)

    if not isinstance(aggiornamenti, dict):
        aggiornamenti = {}

    aggiornamenti = _normalizza_aggiornamenti(aggiornamenti)

    if aggiornamenti:
        # prendi il profilo attuale come dict
        profilo_dict = profilo.model_dump()

        # MERGE AUTOMATICO PER TUTTE LE LISTE
        for campo in ["interessi", "preferenze_viaggio", "preferenze_cibo", "tappe_obbligatorie"]:
            if campo in aggiornamenti:
                esistenti = set(profilo_dict.get(campo, []))
                nuovi = set(aggiornamenti[campo])
                profilo_dict[campo] = list(esistenti.union(nuovi))

        # aggiorna il profilo completo
        profilo = update_user_profile(profilo_dict)


    return {
        "risposta": risposta,
        "profilo_aggiornato": profilo,
        "aggiornamenti": aggiornamenti
    }
