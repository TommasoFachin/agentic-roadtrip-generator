#questo file genera un pdf con repotLab

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.utils import ImageReader
import requests

def genera_pdf_itinerario(itinerario, documento_testuale):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    y = 800
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Road Trip – Itinerario Generato")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Distanza totale: {itinerario.distanza_totale_km} km")
    y -= 20
    c.drawString(50, y, f"Durata totale: {itinerario.durata_totale_ore} ore")
    y -= 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Dettaglio Giorni:")
    y -= 30

    c.setFont("Helvetica", 11)

    for giorno in itinerario.giorni:
        # Controllo per assicurarci di avere spazio a sufficienza per iniziare un nuovo giorno senza tagliarlo
        # Alzato a 300 per garantire spazio anche all'immagine della tappa
        if y < 300:
            c.showPage()
            y = 800

        start_y_tappa = y

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Giorno {giorno.giorno} – {giorno.data}")

        # --- IMMAGINE DELLA TAPPA ---
        image_drawn = False
        if getattr(giorno, "immagine_url", None):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                }
                response = requests.get(giorno.immagine_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    img = ImageReader(BytesIO(response.content))
                    img_w, img_h = 200, 130
                    img_y = y - img_h + 10
                    c.drawImage(img, 350, img_y, width=img_w, height=img_h, preserveAspectRatio=True, anchor='c', mask='auto')
                    image_drawn = True
                else:
                    print(f"Errore download immagine {giorno.citta_tappa}: HTTP {response.status_code}")
            except Exception as e:
                print(f"Errore inserimento immagine per {giorno.citta_tappa}: {e}")

        y -= 20

        c.setFont("Helvetica", 11)
        c.drawString(70, y, f"Distanza: {giorno.distanza_km} km")
        y -= 20
        c.drawString(70, y, f"Durata: {giorno.durata_ore} ore")
        y -= 20
        c.drawString(70, y, f"Tappa: {giorno.citta_tappa}")
        y -= 30

       # --- POI ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y, "POI:")
        y -= 20

        c.setFont("Helvetica", 10)
        for poi in giorno.poi:
            # POI è un dict
            nome = poi.get("name") or "(senza nome)"

            raw_kind = poi.get("kind")
            if isinstance(raw_kind, str):
                kind = raw_kind.split(",")[0].replace("_", " ").capitalize()
            elif isinstance(raw_kind, list):
                kind = raw_kind[0].replace("_", " ").capitalize() if raw_kind else "n/d"
            else:
                kind = "n/d"

            # Sanitizzazione caratteri non supportati
            nome = nome.encode("latin-1", "replace").decode("latin-1")
            kind = kind.encode("latin-1", "replace").decode("latin-1")

            c.drawString(90, y, f"- {nome} ({kind})")
            y -= 15

            if y < 100:
                c.showPage()
                y = 800

        y -= 10 # Spazio extra

        # --- EVENTI ---
        if giorno.eventi:
            if y < 150:
                c.showPage()
                y = 800
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(70, y, "Eventi suggeriti per la serata:")
            y -= 20

            c.setFont("Helvetica", 10)
            for evento in giorno.eventi:
                nome_evento = evento.get("nome", "(Senza nome)")
                nome_evento = nome_evento.encode("latin-1", "replace").decode("latin-1")
                c.drawString(90, y, f"- {nome_evento}")
                y -= 15

                if y < 100:
                    c.showPage()
                    y = 800

        # Evitiamo che il testo del giorno successivo si sovrapponga all'immagine
        if image_drawn:
            min_y = start_y_tappa - 140
            if y > min_y:
                y = min_y

        y -= 20

        if y < 100:
            c.showPage()
            y = 800

    # --- DOCUMENTO TESTUALE ---
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, "Documento Riassuntivo")
    y = 760
    c.setFont("Helvetica", 11)

    for line in documento_testuale.split("\n"):
        # Sanitizza anche il documento LLM
        safe_line = line.encode("latin-1", "replace").decode("latin-1")
        c.drawString(50, y, safe_line)
        y -= 20
        if y < 100:
            c.showPage()
            y = 800

    c.save()
    buffer.seek(0)
    return buffer
