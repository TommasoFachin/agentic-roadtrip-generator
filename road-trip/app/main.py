from fastapi import FastAPI, HTTPException
from app.models import TripRequest
from pydantic import BaseModel
from app.agent.llm_agent import interpreta_richiesta
from app.services.geocoding_service import geocoding_citta, reverse_geocoding
from app.services.routing_service import calcola_percorso
from fastapi.responses import StreamingResponse
from app.services.pdf_service import genera_pdf_itinerario
from app.user_profile_router import router as user_profile_router
from fastapi.concurrency import run_in_threadpool
from app.services.planner_service import (
    costruisci_itinerario,
    calcola_tappe,
    verifica_fattibilita_viaggio
)
from app.services.user_profile_service import get_user_profile, update_user_profile

#modello per l'endpoint interpreta-richiesta, che riceve un testo e restituisce un JSON strutturato secondo TripRequest
class InterpretationRequest(BaseModel):
    testo: str

app = FastAPI()
app.include_router(user_profile_router)

#endpoint per interpretare il testo naturale e restituire un JSON strutturato secondo TripRequest
@app.post("/interpreta-richiesta")
async def interpreta(payload: InterpretationRequest):
    return await interpreta_richiesta(payload.testo)

#utility pe rpreparare i dati del viaggio
def _prepara_dati_viaggio(richiesta: TripRequest):

    profilo = get_user_profile()

    # Geocoding: converte citta in coordinate
    coord_start = geocoding_citta(richiesta.luogo_partenza)
    coord_end = geocoding_citta(richiesta.luogo_destinazione)

    # Costruiamo la lista di tutte le coordinate (partenza -> tappe -> destinazione)
    coordinate_percorso = [coord_start]
    
    tappe_unite = []
    nomi_tappe_visti = set()
    
    # Salviamo i nomi base di partenza e arrivo per non metterli in mezzo
    start_name = richiesta.luogo_partenza.split(',')[0].strip().lower()
    end_name = richiesta.luogo_destinazione.split(',')[0].strip().lower()
    nomi_tappe_visti.add(start_name)
    nomi_tappe_visti.add(end_name)

    def aggiungi_tappa(tappa):
        nome = tappa.split(',')[0].strip().lower()
        if nome not in nomi_tappe_visti:
            tappe_unite.append(tappa)
            nomi_tappe_visti.add(nome)

    if richiesta.tappe_intermedie:
        for t in richiesta.tappe_intermedie:
            aggiungi_tappa(t)
    if profilo.tappe_obbligatorie:
        for t in profilo.tappe_obbligatorie:
            aggiungi_tappa(t)
                
    for tappa in tappe_unite:
        try:
            coord_tappa = geocoding_citta(tappa)
            coordinate_percorso.append(coord_tappa)
        except Exception as e:
            print(f"Errore geocoding tappa intermedia {tappa}: {e}")
                
    coordinate_percorso.append(coord_end)

    # Routing: distanza reale + durata
    percorso = calcola_percorso(coordinate_percorso)

    # STEP 3.1 — Calcolo tappe in base ai km/giorno
    distanza_massima = richiesta.preferenze.distanza_massima_giornaliera
    tappe_info = calcola_tappe(
        distanza_km=percorso["distanza_km"],
        distanza_massima_giornaliera=distanza_massima
    )

    # Calcolo giorni disponibili
    giorni_disponibili = (richiesta.data_arrivo - richiesta.data_partenza).days + 1
    if giorni_disponibili <= 0:
        raise HTTPException(
            status_code=400, 
            detail="La data di arrivo deve essere successiva alla data di partenza."
        )

    # STEP 3.2 — Verifica fattibilità del viaggio
    verifica = verifica_fattibilita_viaggio(
        required_days=tappe_info["required_days"],
        giorni_disponibili=giorni_disponibili
    )

    return tappe_info, verifica, percorso, distanza_massima

#endpoint per generare l'itinerario in formato PDF
@app.post("/genera-itinerario")
async def genera_itinerario(richiesta: TripRequest):
    tappe_info, verifica, percorso, distanza_massima = await run_in_threadpool(_prepara_dati_viaggio, richiesta)

    if not verifica["fattibile"]:
        return {
            "errore": "Viaggio non fattibile",
            "dettagli": verifica,
            "tappe_info": tappe_info,
        }

    itinerario = await costruisci_itinerario(
        percorso,
        richiesta.preferenze,
        distanza_massima,
        richiesta.data_partenza
    )

    documento = f"Itinerario di {len(itinerario.giorni)} giorni generato con successo."

    # --- GENERAZIONE E SALVATAGGIO PDF LOCALE ---
    # Questo salva il file nella cartella del progetto ogni volta che chiami l'API
    pdf_buffer = genera_pdf_itinerario(itinerario, documento)
    with open("itinerario_generato.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())

    # --- PULIZIA PROFILO (MANTIENI INTERESSI) ---
    profilo = get_user_profile()
    profilo_dict = profilo.model_dump()
    profilo_dict["tappe_obbligatorie"] = []
    profilo_dict["preferenze_viaggio"] = []
    profilo_dict["preferenze_cibo"] = []
    update_user_profile(profilo_dict)

    return {
        "tappe_info": tappe_info,
        "verifica": verifica,
        "itinerario": itinerario,
        "documento": documento
    }

#endpoint per generare l'itinerario e restituirlo come file PDF scaricabile
@app.post("/genera-itinerario-pdf")
async def genera_itinerario_pdf(richiesta: TripRequest):
    tappe_info, verifica, percorso, distanza_massima = await run_in_threadpool(_prepara_dati_viaggio, richiesta)

    if not verifica["fattibile"]:
        raise HTTPException(status_code=400, detail=f"Viaggio non fattibile: {verifica['motivo']}")

    itinerario = await costruisci_itinerario(
        percorso,
        richiesta.preferenze,
        distanza_massima,
        richiesta.data_partenza
    )

    documento = f"Itinerario di {len(itinerario.giorni)} giorni generato con successo."

    # --- GENERAZIONE PDF ---
    pdf_buffer = genera_pdf_itinerario(itinerario, documento)

    # --- PULIZIA PROFILO (MANTIENI INTERESSI) ---
    profilo = get_user_profile()
    profilo_dict = profilo.model_dump()
    profilo_dict["tappe_obbligatorie"] = []
    profilo_dict["preferenze_viaggio"] = []
    profilo_dict["preferenze_cibo"] = []
    update_user_profile(profilo_dict)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=itinerario.pdf"}
    )
