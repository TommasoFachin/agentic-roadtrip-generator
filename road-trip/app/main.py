from fastapi import FastAPI, HTTPException
from app.models import TripRequest
from app.agent.llm_agent import genera_documento_finale
from app.services.geocoding_service import geocoding_citta
from app.services.routing_service import calcola_percorso
from fastapi.responses import StreamingResponse
from app.services.pdf_service import genera_pdf_itinerario
from app.services.planner_service import (
    costruisci_itinerario,
    calcola_tappe,
    verifica_fattibilita_viaggio
)

app = FastAPI()

def _prepara_dati_viaggio(richiesta: TripRequest):
    """
    Funzione di utility per centralizzare la logica di calcolo del percorso 
    e delle tappe, evitando duplicazioni tra gli endpoint JSON e PDF.
    """
    # Geocoding: città → coordinate
    coord_start = geocoding_citta(richiesta.luogo_partenza)
    coord_end = geocoding_citta(richiesta.luogo_destinazione)

    lon_start, lat_start = coord_start
    lon_end, lat_end = coord_end

    # Routing: distanza reale + durata
    percorso = calcola_percorso(lon_start, lat_start, lon_end, lat_end)

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

@app.post("/genera-itinerario")
def genera_itinerario(richiesta: TripRequest):
    tappe_info, verifica, percorso, distanza_massima = _prepara_dati_viaggio(richiesta)

    if not verifica["fattibile"]:
        return {
            "errore": "Viaggio non fattibile",
            "dettagli": verifica,
            "tappe_info": tappe_info,
            
        }

    itinerario = costruisci_itinerario(
        percorso,
        richiesta.preferenze,
        distanza_massima,
        richiesta.data_partenza
    )

    # Generazione documento finale (LLM) — FUTURO
    documento = genera_documento_finale(itinerario)

    # --- GENERAZIONE E SALVATAGGIO PDF LOCALE ---
    # Questo salva il file nella cartella del progetto ogni volta che chiami l'API
    pdf_buffer = genera_pdf_itinerario(itinerario, documento)
    with open("itinerario_generato.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())

    return {"tappe_info": tappe_info, "verifica": verifica, "itinerario": itinerario, "documento": documento}

@app.post("/genera-itinerario-pdf")
def genera_itinerario_pdf(richiesta: TripRequest):
    tappe_info, verifica, percorso, distanza_massima = _prepara_dati_viaggio(richiesta)

    if not verifica["fattibile"]:
        raise HTTPException(status_code=400, detail=f"Viaggio non fattibile: {verifica['motivo']}")

    itinerario = costruisci_itinerario(
        percorso,
        richiesta.preferenze,
        distanza_massima,
        richiesta.data_partenza
    )

    # 2. Genera documento testuale (ora semplice, poi con LLM)
    documento = genera_documento_finale(itinerario)

    # 3. Genera PDF
    pdf_buffer = genera_pdf_itinerario(itinerario, documento)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=itinerario.pdf"}
    )
