import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPORT_PATH = os.path.expanduser("~/daniela-os/Cyber_Sentinel_Threat_Report.pdf")


def generate_pdf_report(scan_results, target_ip="192.168.1.1"):
    """Genera un informe táctico de seguridad en PDF."""
    doc = SimpleDocTemplate(REPORT_PATH, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Estilos
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=colors.HexColor("#00F0FF"),
        spaceAfter=12,
    )
    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#CCCCCC"),
        spaceAfter=8,
    )

    # Contenido
    story.append(Paragraph("CYBER SENTINEL - REPORT DE AUDITORÍA", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Objetivo:</b> {target_ip}", normal_style))
    story.append(Paragraph("<b>Estado:</b> Auditoría Completada", normal_style))
    story.append(Spacer(1, 15))

    # Tabla de Resultados
    data = [["Puerto", "Estado", "Riesgo Evaluado"]]
    for port in scan_results:
        risk = "ALTO" if port in [21, 22, 23, 80] else "MEDIO"
        data.append([str(port), "ABIERTO", risk])

    if len(data) == 1:
        data.append(["N/A", "Sin puertos abiertos detectados", "BAJO"])

    t = Table(data, colWidths=[100, 200, 150])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A2E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#00F0FF")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#16213E")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#FFFFFF")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#00F0FF")),
            ]
        )
    )
    story.append(t)

    doc.build(story)
    return REPORT_PATH
