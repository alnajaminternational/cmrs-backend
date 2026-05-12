from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import io

app = Flask(__name__)
CORS(app)

# ── Email Config ──
GMAIL_ADDRESS      = "cv@alnajam.com"
GMAIL_APP_PASSWORD = "anfqdjxzuyjhysoi"
RECIPIENT_EMAIL    = "cv@alnajam.com"


def build_pdf(data):
    """Generate a filled CMRS-style PDF from submission data."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=12*mm,
        bottomMargin=12*mm
    )

    styles = getSampleStyleSheet()
    normal = ParagraphStyle('normal', fontName='Helvetica', fontSize=8.5, leading=11)
    bold   = ParagraphStyle('bold',   fontName='Helvetica-Bold', fontSize=8.5, leading=11)
    small  = ParagraphStyle('small',  fontName='Helvetica', fontSize=7.5, leading=10)
    header_style = ParagraphStyle('header', fontName='Helvetica-Bold', fontSize=10, leading=13, alignment=1)
    title_style  = ParagraphStyle('title',  fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=1)
    section_style = ParagraphStyle('section', fontName='Helvetica-Bold', fontSize=8.5, leading=11)

    story = []

    # ── Header ──
    header_data = [[
        Paragraph("Kingdom of Saudi Arabia\nMinistry of National Guard\nHealth Affairs\nKing Abdulaziz Medical City", bold),
        Paragraph("KAMC\nKAMC", header_style),
        Paragraph("والمملكة العربية السعودية\nوزارة الحرس الوطني\nالشؤون الصحية\nمدينة الملك عبدالعزيز الطبية", bold),
    ]]
    header_tbl = Table(header_data, colWidths=[60*mm, 60*mm, 60*mm])
    header_tbl.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.black),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Title ──
    title_tbl = Table([[Paragraph("Corporate Medical Recruitment Application Form", title_style)]],
                      colWidths=[180*mm])
    title_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#c8c8c8')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 1*mm))

    def section_row(label):
        t = Table([[Paragraph(label, section_style)]], colWidths=[180*mm])
        t.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.8, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
        ]))
        return t

    def two_col_row(label, value, label_w=65*mm):
        t = Table(
            [[Paragraph(label, bold), Paragraph(str(value) if value else '', normal)]],
            colWidths=[label_w, 180*mm - label_w]
        )
        t.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        return t

    # Agency
    story.append(two_col_row("AGENCY NAME:", "ALNAJAM INTERNATIONAL"))
    story.append(two_col_row("POSITION APPLIED FOR:", data.get('position', '')))

    # Biographical
    story.append(section_row("BIOGRAPHICAL DATA:"))
    bio_fields = [
        ("Name of Candidate (as per passport):", data.get('candidate_name', '')),
        ("Full Date of Birth (day-month-year):",  data.get('dob', '')),
        ("Gender:",       data.get('gender', '')),
        ("Nationality:",  data.get('nationality', '')),
        ("Weight:",       data.get('weight', '')),
        ("Height:",       data.get('height', '')),
    ]
    for lbl, val in bio_fields:
        story.append(two_col_row(lbl, val))

    # Qualifications
    story.append(section_row("QUALIFICATIONS: (please indicate the date obtained in month / year format)"))
    for q in data.get('qualifications', []):
        if q and q.strip():
            t = Table([[Paragraph(q, normal)]], colWidths=[180*mm])
            t.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 0.5, colors.black),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(t)
        else:
            t = Table([['']], colWidths=[180*mm])
            t.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 0.5, colors.black),
                ('MINROWHEIGHT', (0,0), (-1,-1), 14),
            ]))
            story.append(t)

    # Training
    story.append(section_row("TRAINING / FELLOWSHIP: (in chronological order with recent training first)"))
    tr_header = Table(
        [[Paragraph("Inclusive Date (month/year)", bold), Paragraph("Discipline / Specialty, Institution, City/State, and Country", bold)]],
        colWidths=[50*mm, 130*mm]
    )
    tr_header.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tr_header)
    for entry in data.get('training', []):
        dates  = entry.get('dates', '')  if isinstance(entry, dict) else ''
        detail = entry.get('detail', '') if isinstance(entry, dict) else ''
        t = Table(
            [[Paragraph(dates, normal), Paragraph(detail, normal)]],
            colWidths=[50*mm, 130*mm]
        )
        t.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('MINROWHEIGHT', (0,0), (-1,-1), 14),
        ]))
        story.append(t)

    # Work Experience
    story.append(section_row("WORK EXPERIENCE: (in chronological order with recent appointment first)"))
    we_header = Table(
        [[Paragraph("Inclusive Date (month/year)", bold), Paragraph("Position, Discipline/Specialty, Institution, City/State, and Country", bold)]],
        colWidths=[50*mm, 130*mm]
    )
    we_header.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(we_header)
    for entry in data.get('work_experience', []):
        dates  = entry.get('dates', '')  if isinstance(entry, dict) else ''
        detail = entry.get('detail', '') if isinstance(entry, dict) else ''
        t = Table(
            [[Paragraph(dates, normal), Paragraph(detail, normal)]],
            colWidths=[50*mm, 130*mm]
        )
        t.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('MINROWHEIGHT', (0,0), (-1,-1), 14),
        ]))
        story.append(t)

    # Remarks
    story.append(section_row("REMARKS / CANDIDATE'S SPECIFIC REQUIREMENT / EXPECTATION (if any):"))
    remarks = data.get('remarks', '')
    t = Table([[Paragraph(str(remarks) if remarks else '', normal)]], colWidths=[180*mm])
    t.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('MINROWHEIGHT', (0,0), (-1,-1), 28),
    ]))
    story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def send_email(pdf_bytes, candidate_name):
    msg = MIMEMultipart()
    msg['From']    = GMAIL_ADDRESS
    msg['To']      = RECIPIENT_EMAIL
    msg['Subject'] = f"CMRS Application — {candidate_name}"

    body = f"""A new CMRS application has been submitted.

Candidate: {candidate_name}

Please find the filled application form attached.

— CMRS Automated Form System
"""
    msg.attach(MIMEText(body, 'plain'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    safe_name = candidate_name.replace(' ', '_')
    part.add_header('Content-Disposition', f'attachment; filename="CMRS_{safe_name}.pdf"')
    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())


@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        candidate_name = data.get('candidate_name', 'Unknown Candidate')
        pdf_bytes = build_pdf(data)
        send_email(pdf_bytes, candidate_name)
        return jsonify({"ok": True})
    except Exception as e:
        print("Error:", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "running"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
