from fastapi import FastAPI, HTTPException
from app.models import TripRequest
from pydantic import BaseModel
import asyncio
import json
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
from fastapi.middleware.cors import CORSMiddleware
from app.services.user_profile_service import get_user_profile, update_user_profile

#modello per l'endpoint interpreta-richiesta, che riceve un testo e restituisce un JSON strutturato secondo TripRequest
class InterpretationRequest(BaseModel):
    testo: str

app = FastAPI()

# Abilitiamo i CORS per permettere al frontend HTML/JS di comunicare con le API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consente a qualsiasi frontend locale di fare richieste
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_profile_router)

#endpoint per interpretare il testo naturale e restituire un JSON strutturato secondo TripRequest
@app.post("/interpreta-richiesta")
async def interpreta(payload: InterpretationRequest):
    return await interpreta_richiesta(payload.testo)


@app.get("/reverse-geocoding")
async def reverse_geocoding_endpoint(lat: float, lon: float):
    citta, country_code = await run_in_threadpool(reverse_geocoding, lat, lon)
    return {
        "citta": citta,
        "country_code": country_code,
    }

#utility pe rpreparare i dati del viaggio
def _prepara_dati_viaggio(richiesta: TripRequest):

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

    if hasattr(richiesta, "tappe_intermedie_utente") and richiesta.tappe_intermedie_utente:
        for t in richiesta.tappe_intermedie_utente:
            aggiungi_tappa(t)
            
    if hasattr(richiesta, "tappe_intermedie") and richiesta.tappe_intermedie:
        for t in richiesta.tappe_intermedie:
            aggiungi_tappa(t)
                
    for tappa in tappe_unite:
        try:
            coord_tappa = geocoding_citta(tappa)
            coordinate_percorso.append(coord_tappa)
        except Exception as e:
            print(f"Errore geocoding tappa intermedia {tappa}: {e}")
                
    coordinate_percorso.append(coord_end)

    # Routing: distanza reale + durata
    percorso_andata = calcola_percorso(coordinate_percorso)
    percorso_finale = percorso_andata

    giorni_disponibili_utente = (richiesta.data_arrivo - richiesta.data_partenza).days + 1

    # 🔥 NUOVA LOGICA ANDATA/RITORNO
    if richiesta.is_round_trip:
        print("INFO: Pianificazione viaggio di andata e ritorno.")
        # Per il ritorno, invertiamo partenza e destinazione
        coordinate_percorso_ritorno = [coord_end, coord_start]
        percorso_ritorno = calcola_percorso(coordinate_percorso_ritorno)

        # Uniamo i due percorsi in un unico viaggio
        percorso_finale = {
            "distanza_km": percorso_andata["distanza_km"] + percorso_ritorno["distanza_km"],
            "durata_sec": percorso_andata["durata_sec"] + percorso_ritorno["durata_sec"],
            "geometry": percorso_andata["geometry"][:-1] + percorso_ritorno["geometry"],
            "way_points": percorso_andata["way_points"]
        }
        # Dividiamo i giorni a metà, arrotondando per difetto.
        # L'ultimo giorno del ritorno potrebbe essere più lungo, ma il planner lo gestirà.
        giorni_disponibili_utente = giorni_disponibili_utente // 2
        print(f"INFO: Giorni per l'andata e ritorno divisi a metà: {giorni_disponibili_utente} giorni per tratta.")

    # --- LOGICA PER ADATTARE IL VIAGGIO ALLA DURATA RICHIESTA ---
    distanza_massima_utente = richiesta.preferenze.distanza_massima_giornaliera

    # Calcoliamo la distanza media giornaliera necessaria per riempire tutti i giorni
    distanza_ideale_giornaliera = 0
    # Usiamo il percorso_finale che può essere solo andata o A/R
    if giorni_disponibili_utente > 0 and percorso_finale["distanza_km"] > 0:
        distanza_ideale_giornaliera = percorso_finale["distanza_km"] / giorni_disponibili_utente

    # Se la distanza ideale è inferiore al massimo dell'utente, la usiamo per "allungare" il viaggio.
    # Altrimenti, usiamo il massimo dell'utente (il viaggio sarà più breve o non fattibile).
    if distanza_ideale_giornaliera > 0 and distanza_ideale_giornaliera < distanza_massima_utente:
        print(f"INFO: Adatto il viaggio a {giorni_disponibili_utente} giorni. Distanza giornaliera impostata a {int(distanza_ideale_giornaliera)} km.")
        distanza_massima_effettiva = distanza_ideale_giornaliera
    else:
        distanza_massima_effettiva = distanza_massima_utente

    # Usiamo la distanza effettiva per il calcolo delle tappe
    tappe_info = calcola_tappe(percorso_finale["distanza_km"], distanza_massima_effettiva)
    # ----------------------------------------------------------------

    # Calcolo giorni disponibili
    giorni_disponibili = (richiesta.data_arrivo - richiesta.data_partenza).days + 1
    if giorni_disponibili <= 0:
        raise HTTPException(
            status_code=400, 
            detail="La data di arrivo deve essere successiva alla data di partenza."
        )

    # STEP 3.2 — Verifica fattibilità del viaggio
    verifica = verifica_fattibilita_viaggio( # type: ignore
        required_days=tappe_info["required_days"],
        giorni_disponibili=giorni_disponibili
    )

    return tappe_info, verifica, percorso_finale, distanza_massima_effettiva

#endpoint per generare l'itinerario in formato PDF
@app.post("/genera-itinerario")
async def genera_itinerario(richiesta: TripRequest):
    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    risultato_finale: dict[str, object] = {}
    errore_finale: dict[str, str] = {}

    async def manda_evento(evento: dict) -> None:
        await queue.put(evento)

    async def costruisci_e_salva() -> None:
        try:
            await manda_evento({"type": "status", "message": "Preparo i dati del viaggio..."})
            tappe_info, verifica, percorso, distanza_massima = await run_in_threadpool(_prepara_dati_viaggio, richiesta)

            if not verifica["fattibile"]:
                errore_finale["message"] = "Viaggio non fattibile"
                errore_finale["details"] = json.dumps({
                    "motivo": verifica.get("motivo"),
                    "tappe_info": tappe_info,
                    "verifica": verifica,
                }, ensure_ascii=False, default=str)
                return

            richiesta.preferenze.distanza_massima_giornaliera = distanza_massima

            async def on_day(giorno):
                await manda_evento({"type": "day", "day": giorno.model_dump(mode="json")})

            if richiesta.is_round_trip:
                await manda_evento({"type": "status", "message": "Pianifico l'andata..."})
                percorso_andata = calcola_percorso(
                    [geocoding_citta(richiesta.luogo_partenza)] +
                    [geocoding_citta(t) for t in richiesta.tappe_intermedie_utente] +
                    [geocoding_citta(richiesta.luogo_destinazione)]
                )
                itinerario_andata = await costruisci_itinerario(percorso_andata, richiesta, on_day=on_day)

                citta_tappe_andata = [g.citta_tappa for g in itinerario_andata.giorni]

                await manda_evento({"type": "status", "message": "Pianifico il ritorno..."})
                richiesta_ritorno = richiesta.model_copy(deep=True)
                richiesta_ritorno.luogo_partenza, richiesta_ritorno.luogo_destinazione = richiesta.luogo_destinazione, richiesta.luogo_partenza
                richiesta_ritorno.tappe_intermedie_utente = []

                percorso_ritorno = calcola_percorso(
                    [geocoding_citta(richiesta_ritorno.luogo_partenza), geocoding_citta(richiesta_ritorno.luogo_destinazione)]
                )

                giorno_partenza_ritorno = len(itinerario_andata.giorni) + 1
                itinerario_ritorno = await costruisci_itinerario(
                    percorso_ritorno,
                    richiesta_ritorno,
                    citta_da_evitare=citta_tappe_andata,
                    giorno_partenza=giorno_partenza_ritorno,
                    on_day=on_day,
                )

                itinerario = itinerario_andata
                itinerario.giorni.extend(itinerario_ritorno.giorni)
            else:
                await manda_evento({"type": "status", "message": "Pianifico il viaggio..."})
                itinerario = await costruisci_itinerario(percorso, richiesta, on_day=on_day)

            documento = f"Itinerario di {len(itinerario.giorni)} giorni generato con successo."

            pdf_buffer = genera_pdf_itinerario(itinerario, documento)
            with open("itinerario_generato.pdf", "wb") as f:
                f.write(pdf_buffer.getvalue())

            profilo = get_user_profile()
            profilo_dict = profilo.model_dump()
            profilo_dict["tappe_obbligatorie"] = []
            profilo_dict["preferenze_viaggio"] = []
            profilo_dict["preferenze_cibo"] = []
            update_user_profile(profilo_dict)

            risultato_finale.update({
                "tappe_info": tappe_info,
                "verifica": verifica,
                "itinerario": itinerario.model_dump(mode="json"),
                "documento": documento,
            })
        except Exception as exc:
            errore_finale["message"] = str(exc)
        finally:
            await queue.put(None)

    task = asyncio.create_task(costruisci_e_salva())

    async def event_stream():
        while True:
            evento = await queue.get()
            if evento is None:
                break
            yield (json.dumps(evento, ensure_ascii=False, default=str) + "\n").encode("utf-8")

        await task

        if errore_finale:
            yield (json.dumps({"type": "error", **errore_finale}, ensure_ascii=False, default=str) + "\n").encode("utf-8")
            return

        yield (json.dumps({"type": "done", **risultato_finale}, ensure_ascii=False, default=str) + "\n").encode("utf-8")

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

#endpoint per generare l'itinerario e restituirlo come file PDF scaricabile
@app.post("/genera-itinerario-pdf")
async def genera_itinerario_pdf(richiesta: TripRequest):
    tappe_info, verifica, percorso, distanza_massima = await run_in_threadpool(_prepara_dati_viaggio, richiesta)

    if not verifica["fattibile"]:
        raise HTTPException(status_code=400, detail=f"Viaggio non fattibile: {verifica['motivo']}")

    # 🔥 FIX: Aggiorniamo la richiesta con la distanza giornaliera effettiva
    # per far sì che il viaggio si adatti ai giorni disponibili.
    richiesta.preferenze.distanza_massima_giornaliera = distanza_massima
    # Passiamo l'intera richiesta, che contiene tutte le info necessarie
    
    # 🔥 FIX ANDATA/RITORNO: Se è un round trip, passiamo al planner SOLO il percorso di andata.
    percorso_da_usare = percorso if not richiesta.is_round_trip else calcola_percorso([geocoding_citta(richiesta.luogo_partenza)] + [geocoding_citta(t) for t in richiesta.tappe_intermedie_utente] + [geocoding_citta(richiesta.luogo_destinazione)])

    itinerario = await costruisci_itinerario(percorso_da_usare, richiesta)

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
