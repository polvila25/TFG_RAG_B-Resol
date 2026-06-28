import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors

# Colors de la marca b-resol (estètica de la interfície)
BRESOL_RED = colors.HexColor("#8B263E")
BRESOL_PINK = colors.HexColor("#E5A9B8")
BRESOL_LIGHT_GREY = colors.HexColor("#F5F5F5")
BRESOL_DARK_GREY = colors.HexColor("#333333")

def generate_bresol_report(
    case_number: str,
    date_str: str,
    reporter_mode: str,
    situation_description: str,
    risk_category_label: str,
    affected_people: list,
    authors: list,
    specialists: str,
    actions_protocol: str
) -> bytes:
    """
    Genera el PDF d'actuació de b-resol.
    affected_people / authors son llistes de diccionaris: [{'name': '...', 'course': '...'}]
    """
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Estils personalitzats
    title_style = ParagraphStyle(
        'BresolTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=BRESOL_RED,
        spaceAfter=20,
        alignment=TA_LEFT,
        fontName="Helvetica-Bold"
    )
    
    subtitle_style = ParagraphStyle(
        'BresolSubtitle',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=BRESOL_RED,
        spaceAfter=10,
        spaceBefore=15,
        fontName="Helvetica-Bold",
        textTransform="uppercase"
    )
    
    normal_style = ParagraphStyle(
        'BresolNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=BRESOL_DARK_GREY,
        spaceAfter=8,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    bold_style = ParagraphStyle(
        'BresolBold',
        parent=normal_style,
        fontName="Helvetica-Bold"
    )

    elements = []
    
    # --- CAPÇALERA / DASHBOARD ---
    elements.append(Paragraph("DASHBOARD D'ACTUACIÓ", title_style))
    
    header_data = [
        [Paragraph(f"<b>NÚM. DEL CLICK:</b> {case_number}", normal_style),
         Paragraph(f"<b>DATA:</b> {date_str}", normal_style),
         Paragraph(f"<b>MODE:</b> {reporter_mode}", normal_style)]
    ]
    
    header_table = Table(header_data, colWidths=['33%', '33%', '34%'])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TEXTCOLOR', (0,0), (-1,-1), BRESOL_RED),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, BRESOL_RED),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # --- IDENTIFICACIÓ ---
    elements.append(Paragraph("IDENTIFICACIÓ", subtitle_style))
    
    # Persones Afectades
    elements.append(Paragraph("PERSONES AFECTADES", bold_style))
    
    def create_people_table(people_list):
        data = [["NOM I COGNOMS", "CURS O CATEGORITZACIÓ"]]
        if not people_list:
            data.append(["Cap dada disponible en aquesta taula", ""])
        else:
            for p in people_list:
                name = p.get('name', '').strip()
                course = p.get('course', '').strip()
                if not name and not course:
                    continue
                data.append([name if name else "No especificat", course if course else "No especificat"])
            
            # Si només s'ha afegit la capçalera (tots els elements estaven buits)
            if len(data) == 1:
                data.append(["Cap dada disponible en aquesta taula", ""])
                
        t = Table(data, colWidths=['60%', '40%'])
        t.setStyle(TableStyle([
            ('TEXTCOLOR', (0,0), (-1,0), BRESOL_RED),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 5),
            ('TOPPADDING', (0,0), (-1,0), 5),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ]))
        return t

    elements.append(create_people_table(affected_people))
    elements.append(Spacer(1, 15))
    
    # Autors dels Fets
    elements.append(Paragraph("AUTORS DELS FETS", bold_style))
    elements.append(create_people_table(authors))
    elements.append(Spacer(1, 20))
    
    # --- CARACTERÍSTIQUES ---
    elements.append(Paragraph("CARACTERÍSTIQUES", subtitle_style))
    
    elements.append(Paragraph("<b>SITUACIÓ / CONDUCTA DETECTADA:</b>", normal_style))
    elements.append(Paragraph(risk_category_label, normal_style))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("<b>RESUM / DESCRIPCIÓ DE LA SITUACIÓ:</b>", normal_style))
    # Replace newlines with <br/> for ReportLab Paragraph
    desc_html = str(situation_description).replace('\n', '<br/>')
    elements.append(Paragraph(desc_html, normal_style))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("<b>ESPECIALISTES I TERCERS EXTERNS:</b>", normal_style))
    spec_html = str(specialists).replace('\n', '<br/>') if specialists else "No especificat"
    elements.append(Paragraph(spec_html, normal_style))
    elements.append(Spacer(1, 20))
    
    # --- ACTUACIONS ---
    elements.append(Paragraph("ACTUACIONS / PROTOCOL A SEGUIR", subtitle_style))
    
    act_html = str(actions_protocol).replace('\n', '<br/>')
    elements.append(Paragraph(act_html, normal_style))
    
    # Generar document
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
