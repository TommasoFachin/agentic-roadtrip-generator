# Road Trip Planner AI

Questo progetto è un'applicazione web per la pianificazione di viaggi "on the road" potenziata da Intelligenza Artificiale. L'utente può descrivere il viaggio desiderato in linguaggio naturale e l'applicazione genera un itinerario dettagliato giorno per giorno, completo di tappe, punti di interesse (POI), eventi e suggerimenti per hotel e ristoranti.

## Struttura del Progetto
-   **Backend**: Sviluppato in Python con **FastAPI**. Gestisce la logica di business, l'interazione con i modelli AI (tramite Groq) e le API esterne.
-   **Frontend**: Un'applicazione web sviluppata con **React** (e Vite) che comunica con il backend per offrire un'interfaccia utente dinamica.
-   **Modelli Dati**: Utilizza **Pydantic** per definire modelli di dati robusti e validati, usati in tutta l'applicazione.
-   **Agenti AI**: Utilizzano `pydantic-ai` per interagire con modelli LLM (Llama 3.1 via Groq) per interpretare le richieste, selezionare POI, eventi e altro.

---

## Prerequisiti

Prima di iniziare, assicurati di avere installato sul tuo sistema:

-   Python 3.9+
-   Node.js (include npm) per avviare un server web locale per il frontend.

---

## Installazione e Avvio

Segui questi passaggi per configurare ed eseguire il progetto localmente!: 

### 1. Clona il Repository

Ottieni una copia locale del progetto:

bash: 
git clone <URL_DEL_REPOSITORY>
cd road-trip



### 2. Configura il Backend (Python)

Il backend richiede diverse chiavi API per funzionare correttamente.

#### a. Crea il file `.env`: (se sei una persona fidata contattami che ti mando il mio), se no: 

Nella cartella principale del progetto (`road-trip/`), crea un file chiamato `.env` e inserisci le seguenti chiavi.

```ini
# 1. Groq (Obbligatoria) - Per far funzionare gli agenti AI
# Ottieni la chiave da https://console.groq.com/keys
GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 2. OpenRouteService (Obbligatoria) - Per il calcolo dei percorsi stradali
# Ottieni la chiave da https://openrouteservice.org/dev/#/signup
ORS_API_KEY="5b3ce3597851110001cf6241xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 3. OpenTripMap (Obbligatoria) - Per la ricerca di Punti di Interesse (POI)
# Ottieni la chiave da https://opentripmap.io/product (il piano gratuito è sufficiente)
OPENTRIPMAP_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 4. GeoNames (Obbligatoria) - Per dati su popolazione e città
# Crea un account su http://www.geonames.org/login
GEONAMES_USERNAME="tuo_username_geonames"

# 5. Ticketmaster (Opzionale) - Per la ricerca di eventi
# Ottieni la chiave da https://developer.ticketmaster.com/
TICKETMASTER_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 6. Eventbrite (Opzionale) - Per la ricerca di eventi
# Ottieni il token da https://www.eventbrite.com/platform/api-keys/
EVENTBRITE_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxx"
```

#### b. Installa le dipendenze Python

Crea un ambiente virtuale e installa i pacchetti necessari.

```bash
Crea un ambiente virtuale
python -m venv venv

# Attiva l'ambiente virtuale
# Su Windows:
venv\Scripts\activate
# Su macOS/Linux:
source venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt
```

#### c. Avvia il server FastAPI

Una volta attivate le dipendenze, avvia il server di backend.

```bash
uvicorn app.main:app --reload
```

Il backend sarà in esecuzione su `http://127.0.0.1:8000`.

### 3. Avvia il Frontend

Il frontend è un'applicazione web basata su Node.js e va avviato con il suo server di sviluppo.

#### a. Installa le dipendenze del frontend

Dalla cartella principale (`road-trip/`), naviga nella sottocartella `frontend/` e installa i pacchetti necessari.

```bash
# Naviga nella cartella del frontend
cd frontend

# Installa le dipendenze (solo la prima volta)
npm install
```

#### b. Avvia il server di sviluppo
```bash
# Avvia il server
npm run dev
```

Il frontend sarà accessibile all'indirizzo indicato nel terminale (solitamente `http://127.0.0.1:8080`).

---

## ✅ Utilizzo

Una volta che sia il backend che il frontend sono in esecuzione, apri l'URL del frontend nel tuo browser. Ora puoi iniziare a pianificare il tuo viaggio!
