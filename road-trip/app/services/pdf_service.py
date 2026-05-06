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
        c.drawString(50, y, f"Giorno {giorno.giorno} – {giorno.data}")
        y -= 20
        c.drawString(70, y, f"Distanza: {giorno.distanza_km} km")
        y -= 20
        c.drawString(70, y, f"Durata: {giorno.durata_ore} ore")
        y -= 20
        c.drawString(70, y, f"Tappa: {giorno.citta_tappa}")
        y -= 30

        if y < 100:
            c.showPage()
            y = 800

    # Aggiungi il documento testuale generato dall’LLM
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, "Documento Riassuntivo")
    y = 760
    c.setFont("Helvetica", 11)

    for line in documento_testuale.split("\n"):
        c.drawString(50, y, line)
        y -= 20
        if y < 100:
            c.showPage()
            y = 800

    c.save()
    buffer.seek(0)
    return buffer
