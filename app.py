from flask import Flask, request, jsonify, make_response
import smtplib, os, io, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

app = Flask(__name__)

pdfmetrics.registerFont(TTFont('DejaVu',  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

LOGO_B64 = "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"

def ar(text): return get_display(arabic_reshaper.reshape(text))

def corsify(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    return response

@app.after_request
def after_request(response): return corsify(response)

@app.route('/submit', methods=['OPTIONS'])
@app.route('/health', methods=['OPTIONS'])
def options(): return corsify(make_response('', 200))

GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "cv@alnajam.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL    = os.environ.get("RECIPIENT_EMAIL", "cv@alnajam.com")

def build_pdf(d):
    PAGE_W, PAGE_H = A4
    MARGIN = 14*mm
    W = PAGE_W - 2*MARGIN

    ROW_H  = 7.2*mm
    ROW_H2 = 12.2*mm
    SEC_H  = 5*mm
    SEC_H2 = 9*mm
    COL_H  = 6*mm

    N   = ParagraphStyle('n',   fontName='Helvetica',             fontSize=7.5, leading=9)
    B   = ParagraphStyle('b',   fontName='Helvetica-Bold',        fontSize=7.5, leading=9)
    BI  = ParagraphStyle('bi',  fontName='Helvetica-BoldOblique', fontSize=8.5, leading=11)
    T   = ParagraphStyle('t',   fontName='Helvetica-Bold',        fontSize=10,  leading=12, alignment=1)
    EL  = ParagraphStyle('el',  fontName='Helvetica-Bold',        fontSize=7.5, leading=10)
    ARB = ParagraphStyle('arb', fontName='DejaVuB',               fontSize=8,   leading=11, alignment=2)

    def p(t, s=None): return Paragraph(str(t or ''), s or N)

    BOX  = [('BOX',(0,0),(-1,-1),0.5,colors.black),
            ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1),
            ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]
    GRID = BOX + [('INNERGRID',(0,0),(-1,-1),0.5,colors.black),('VALIGN',(0,0),(-1,-1),'MIDDLE')]

    def sec(bold, italic='', h=None):
        txt = f'<b>{bold}</b> <i>{italic}</i>' if italic else f'<b>{bold}</b>'
        t = Table([[Paragraph(txt, N)]], colWidths=[W], rowHeights=[h or SEC_H])
        t.setStyle(TableStyle(BOX)); return t

    def bio_row(l1, l2, val, h=None):
        lbl = Paragraph(f'<b>{l1}</b><br/><i>{l2}</i>', N) if l2 else p(l1, B)
        t = Table([[lbl, p(val or '\u00a0')]], colWidths=[60*mm, W-60*mm], rowHeights=[h or ROW_H])
        t.setStyle(TableStyle(GRID + [('VALIGN',(0,0),(0,0),'TOP')])); return t

    def data_row(left, right, lw=50*mm, h=None):
        lp = left  if isinstance(left,  Paragraph) else p(left  or '\u00a0')
        rp = right if isinstance(right, Paragraph) else p(right or '\u00a0')
        t = Table([[lp, rp]], colWidths=[lw, W-lw], rowHeights=[h or ROW_H])
        t.setStyle(TableStyle(GRID)); return t

    def full_row(txt, s=None, h=None):
        t = Table([[p(txt or '\u00a0', s)]], colWidths=[W], rowHeights=[h or ROW_H])
        t.setStyle(TableStyle(BOX)); return t

    arabic_text = (ar("والمملكة العربية السعودية") + "<br/>" + ar("وزارة الحرس الوطني") +
                   "<br/>" + ar("الشؤون الصحية") + "<br/>" + ar("مدينة الملك عبدالعزيز الطبية"))

    logo_img = Image(io.BytesIO(base64.b64decode(LOGO_B64)), width=18*mm, height=18*mm)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=MARGIN, leftMargin=MARGIN, topMargin=6*mm, bottomMargin=6*mm)

    story = []

    hdr = Table([[
        Paragraph("<b>Kingdom of Saudi Arabia</b><br/><b>Ministry of National Guard</b><br/><b>Health Affairs</b><br/><b>King Abdulaziz Medical City</b>", EL),
        logo_img,
        Paragraph(arabic_text, ARB),
    ]], colWidths=[62*mm, 60*mm, 62*mm], rowHeights=[19*mm])
    hdr.setStyle(TableStyle([
        ('ALIGN',(0,0),(0,0),'LEFT'),('ALIGN',(1,0),(1,0),'CENTER'),('ALIGN',(2,0),(2,0),'RIGHT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 1*mm))

    ttl = Table([[p("Corporate Medical Recruitment Application Form", T)]], colWidths=[W], rowHeights=[7*mm])
    ttl.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.8,colors.black),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    story.append(ttl)
    story.append(Spacer(1, 1*mm))

    story.append(full_row('AGENCY NAME: ALNAJAM INTERNATIONAL', BI))
    story.append(full_row('POSITION APPLIED FOR: ' + (d.get('position','') or ''), BI))

    t = Table([[p('BIOGRAPHICAL DATA:', B)]], colWidths=[W], rowHeights=[SEC_H])
    t.setStyle(TableStyle(BOX)); story.append(t)

    story.append(bio_row('Name of Candidate:', '(as per passport)', d.get('candidate_name',''), ROW_H2))
    story.append(bio_row('Full Date of Birth:', '(day-month-year)', d.get('dob',''), ROW_H2))
    story.append(bio_row('Gender:',      '', d.get('gender','')))
    story.append(bio_row('Nationality:', '', d.get('nationality','')))
    story.append(bio_row('Weight:',      '', d.get('weight','')))
    story.append(bio_row('Height:',      '', d.get('height','')))

    story.append(sec('QUALIFICATIONS:', 'please indicate the date obtained in month / year format'))
    for i in range(1,4):
        story.append(data_row(d.get(f'qual_date_{i}',''), d.get(f'qual_desc_{i}','')))

    story.append(sec('TRAINING / FELLOWSHIP:', 'in chronological order with recent training first in month-year format'))
    story.append(data_row(p('Inclusive Date (in month/year format)', B),
                           p('Discipline / Specialty, Institution, City/State, and Country', B), h=COL_H))
    for i in range(1,6):
        story.append(data_row(d.get(f'train_date_{i}',''), d.get(f'train_desc_{i}','')))

    story.append(sec('WORK EXPERIENCE:',
        'in chronological order with recent appointment first; for current employment, kindly indicate the start date in month-year format.',
        h=SEC_H2))
    story.append(data_row(p('Inclusive Date (in month/year format)', B),
                           p('Position, Discipline/Specialty, Institution, City/State, and Country', B), h=COL_H))
    for i in range(1,10):
        story.append(data_row(d.get(f'work_date_{i}',''), d.get(f'work_desc_{i}','')))

    story.append(sec("REMARKS / CANDIDATE'S SPECIFIC REQUIREMENT / EXPECTATION", 'if any:'))
    for i in range(1,4):
        story.append(data_row(d.get(f'remarks_date_{i}',''), d.get(f'remarks_desc_{i}','')))

    doc.build(story)
    buf.seek(0)
    return buf.read()

def send_email(pdf_bytes, candidate_name, position):
    msg = MIMEMultipart()
    msg['From']    = GMAIL_ADDRESS
    msg['To']      = RECIPIENT_EMAIL
    msg['Subject'] = f"CMRS Application — {candidate_name} | {position}"
    msg.attach(MIMEText(
        f"A new CMRS application has been submitted.\n\n"
        f"Candidate: {candidate_name}\nPosition:  {position}\n\n"
        f"Please find the filled application form attached.\n\n"
        f"— CMRS Automated Form System", 'plain'))
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    safe = candidate_name.replace(' ', '_')
    part.add_header('Content-Disposition', f'attachment; filename="CMRS_{safe}.pdf"')
    msg.attach(part)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        s.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        name     = data.get('candidate_name', 'Unknown Candidate')
        position = data.get('position', 'Not specified')
        pdf      = build_pdf(data)
        send_email(pdf, name, position)
        return jsonify({"ok": True})
    except Exception as e:
        print("SUBMIT ERROR:", e)
        import traceback; traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health(): return jsonify({"status": "running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
