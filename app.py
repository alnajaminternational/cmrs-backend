from flask import Flask, request, jsonify, make_response
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
import io, os

app = Flask(__name__)

def corsify(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    return response

@app.after_request
def after_request(response):
    return corsify(response)

@app.route('/submit', methods=['OPTIONS'])
@app.route('/health', methods=['OPTIONS'])
def options():
    return corsify(make_response('', 200))

GMAIL_ADDRESS      = "cv@alnajam.com"
GMAIL_APP_PASSWORD = os.environ.get("iluztamkivdgzbtt")
RECIPIENT_EMAIL    = "cv@alnajam.com"

def build_pdf(d):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm)

    N = ParagraphStyle('n', fontName='Helvetica',      fontSize=8.5, leading=11)
    B = ParagraphStyle('b', fontName='Helvetica-Bold', fontSize=8.5, leading=11)
    T = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=11,  leading=14, alignment=1)

    BOX  = [('BOX',(0,0),(-1,-1),0.5,colors.black),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),4),('MINROWHEIGHT',(0,0),(-1,-1),14)]
    GRID = BOX + [('INNERGRID',(0,0),(-1,-1),0.5,colors.black),('VALIGN',(0,0),(-1,-1),'MIDDLE')]

    def p(text, style=None):
        return Paragraph(str(text or ''), style or N)

    def sec(label):
        t = Table([[p(label,B)]], colWidths=[180*mm])
        t.setStyle(TableStyle(BOX))
        return t

    def row2(lbl, val, lw=65*mm):
        t = Table([[p(lbl,B), p(val)]], colWidths=[lw, 180*mm-lw])
        t.setStyle(TableStyle(GRID))
        return t

    def tbl2(left, right, lw=50*mm):
        lp = left  if isinstance(left,  Paragraph) else p(left)
        rp = right if isinstance(right, Paragraph) else p(right)
        t = Table([[lp, rp]], colWidths=[lw, 180*mm-lw])
        t.setStyle(TableStyle(GRID))
        return t

    def fullrow(val):
        t = Table([[p(val)]], colWidths=[180*mm])
        t.setStyle(TableStyle(BOX))
        return t

    story = []

    # Header
    hdr = Table([[
        p("Kingdom of Saudi Arabia\nMinistry of National Guard\nHealth Affairs\nKing Abdulaziz Medical City", B),
        p("[ KAMC ]", ParagraphStyle('c', fontName='Helvetica-Bold', fontSize=10, alignment=1)),
        p("والمملكة العربية السعودية\nوزارة الحرس الوطني\nالشؤون الصحية\nمدينة الملك عبدالعزيز الطبية", B),
    ]], colWidths=[60*mm, 60*mm, 60*mm])
    hdr.setStyle(TableStyle([
        ('ALIGN',(0,0),(0,0),'LEFT'),('ALIGN',(1,0),(1,0),'CENTER'),('ALIGN',(2,0),(2,0),'RIGHT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LINEBELOW',(0,0),(-1,-1),1.5,colors.black),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 3*mm))

    ttl = Table([[p("Corporate Medical Recruitment Application Form", T)]], colWidths=[180*mm])
    ttl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#c8c8c8')),
        ('BOX',(0,0),(-1,-1),0.8,colors.black),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    story.append(ttl)
    story.append(Spacer(1, 1*mm))

    story.append(row2("AGENCY NAME:", "ALNAJAM INTERNATIONAL"))
    story.append(row2("POSITION APPLIED FOR:", d.get('position','')))
    story.append(sec("BIOGRAPHICAL DATA:"))
    story.append(row2("Name of Candidate (as per passport):", d.get('candidate_name','')))
    story.append(row2("Full Date of Birth (day-month-year):", d.get('dob','')))
    story.append(row2("Gender:",      d.get('gender','')))
    story.append(row2("Nationality:", d.get('nationality','')))
    story.append(row2("Weight:",      d.get('weight','')))
    story.append(row2("Height:",      d.get('height','')))

    story.append(sec("QUALIFICATIONS: (please indicate the date obtained in month / year format)"))
    for i in range(1,4):
        story.append(fullrow(f"{d.get(f'qual_date_{i}','')}  {d.get(f'qual_desc_{i}','')}".strip()))

    story.append(sec("TRAINING / FELLOWSHIP: (in chronological order with recent training first)"))
    story.append(tbl2(p("Inclusive Date (month/year)",B), p("Discipline / Specialty, Institution, City/State, and Country",B)))
    for i in range(1,6):
        story.append(tbl2(d.get(f'train_date_{i}',''), d.get(f'train_desc_{i}','')))

    story.append(sec("WORK EXPERIENCE: (in chronological order with recent appointment first)"))
    story.append(tbl2(p("Inclusive Date (month/year)",B), p("Position, Discipline/Specialty, Institution, City/State, and Country",B)))
    for i in range(1,10):
        story.append(tbl2(d.get(f'work_date_{i}',''), d.get(f'work_desc_{i}','')))

    story.append(sec("REMARKS / CANDIDATE'S SPECIFIC REQUIREMENT / EXPECTATION (if any):"))
    rem = Table([[p(d.get('remarks',''))]], colWidths=[180*mm])
    rem.setStyle(TableStyle(BOX + [('MINROWHEIGHT',(0,0),(-1,-1),28)]))
    story.append(rem)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def send_email(pdf_bytes, candidate_name, position):
    msg = MIMEMultipart()
    msg['From']    = GMAIL_ADDRESS
    msg['To']      = RECIPIENT_EMAIL
    msg['Subject'] = f"CMRS Application — {candidate_name} | {position}"
    msg.attach(MIMEText(
        f"A new CMRS application has been submitted.\n\n"
        f"Candidate: {candidate_name}\n"
        f"Position:  {position}\n\n"
        f"Please find the filled application form attached.\n\n"
        f"— CMRS Automated Form System", 'plain'))
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
        f'attachment; filename="CMRS_{candidate_name.replace(" ","_")}.pdf"')
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
def health():
    return jsonify({"status": "running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
