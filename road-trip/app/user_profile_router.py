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
         "interessi_poi": [...],
         "interessi_eventi": [...],
         "stile_viaggio": "economico"
      }
    }
    in:
    {
      "interessi_poi": [...],
      "interessi_eventi": [...],
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
    # Questa funzione ora restituisce sia gli aggiornamenti che la risposta naturale
    risultato = await interpreta_messaggio_chatbot(messaggio, profilo.model_dump()) 
    aggiornamenti = risultato.get("aggiornamenti", {})

    if not isinstance(aggiornamenti, dict):
        aggiornamenti = {}

    aggiornamenti = _normalizza_aggiornamenti(aggiornamenti)

    # 🔥 FIX 1: se le liste sono un dict (errore dell'LLM), ignorale
    if "interessi_poi" in aggiornamenti and isinstance(aggiornamenti["interessi_poi"], dict):
        aggiornamenti["interessi_poi"] = []
    if "interessi_eventi" in aggiornamenti and isinstance(aggiornamenti["interessi_eventi"], dict):
        aggiornamenti["interessi_eventi"] = []

    if aggiornamenti:
        # prendi il profilo attuale come dict
        profilo_dict = profilo.model_dump()


        # MERGE AUTOMATICO PER TUTTE LE LISTE
        for campo in ["interessi_poi", "interessi_eventi", "preferenze_viaggio", "preferenze_cibo", "tappe_obbligatorie"]:
            if campo in aggiornamenti:
                esistenti = set(profilo_dict.get(campo, []))
                
                valori_raw = aggiornamenti[campo]
                # Gestione anti-crash per liste o dizionari anomali dall'LLM
                if isinstance(valori_raw, dict):
                    valori_raw = [f"{k}: {v}" for k, v in valori_raw.items()]
                elif not isinstance(valori_raw, list):
                    valori_raw = [valori_raw]
                
                nuovi = set(str(v) for v in valori_raw)
                profilo_dict[campo] = list(esistenti.union(nuovi))

        # aggiorna il profilo completo
        profilo = update_user_profile(profilo_dict)


    return {
        "risposta": risultato.get("risposta", "Ok, ho capito."),
        "profilo_aggiornato": profilo,
        "aggiornamenti": aggiornamenti
    }
