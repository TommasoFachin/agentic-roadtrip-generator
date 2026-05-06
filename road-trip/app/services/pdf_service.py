from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

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
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Giorno {giorno.giorno} – {giorno.data}")
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
                kind = raw_kind
            elif isinstance(raw_kind, list):
                kind = ", ".join(raw_kind)
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
