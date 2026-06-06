from flask import Flask, request, jsonify, make_response, send_file
import smtplib, os, io, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import arabic_reshaper
from bidi.algorithm import get_display

app = Flask(__name__)

pdfmetrics.registerFont(TTFont('DejaVu',  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

LOGO_B64 = ""  # Fetched at runtime from Drive

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
@app.route('/generate', methods=['OPTIONS'])
def options(): return corsify(make_response('', 200))

GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "cv@alnajam.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL    = os.environ.get("RECIPIENT_EMAIL", "cv@alnajam.com")

# ═══════════════════════════════════════════════════════════════════════════
# CRMS PDF (existing — unchanged)
# ═══════════════════════════════════════════════════════════════════════════

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

    try:
        try:
            logo_b64 = d.get('logo_base64', '')
            if logo_b64:
                logo_img = Image(io.BytesIO(base64.b64decode(logo_b64)), width=18*mm, height=18*mm)
            else:
                raise ValueError('No logo')
        except Exception as le:
            print('Logo error:', le)
            logo_img = Paragraph('<b>AL NAJAM</b>', N)
    except Exception:
        logo_img = Paragraph('', N)

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
    remarks = d.get('remarks', '')
    story.append(data_row('', remarks or ''))
    story.append(data_row('', ''))
    story.append(data_row('', ''))

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

# ═══════════════════════════════════════════════════════════════════════════
# AL NAJAM CV PDF (new — added below, nothing above changed)
# ═══════════════════════════════════════════════════════════════════════════

AN_RED   = colors.HexColor('#C62D33')
AN_GOLD  = colors.HexColor('#B8860B')
AN_DARK  = colors.HexColor('#2C2C2C')
AN_LTRED = colors.HexColor('#FFF5F5')
AN_GREY  = colors.HexColor('#888888')
AN_LGREY = colors.HexColor('#F5F5F5')
AN_WHITE = colors.white

AN_W, AN_H = A4
AN_ML = 10*mm; AN_MR = 10*mm; AN_MT = 8*mm; AN_MB = 10*mm
AN_TW = AN_W - AN_ML - AN_MR

def AN_S(size=10, bold=False, color=colors.black, align=TA_LEFT):
    return ParagraphStyle('ans', fontSize=size,
        fontName='Helvetica-Bold' if bold else 'Helvetica',
        textColor=color, alignment=align, leading=size*1.4,
        spaceAfter=0, spaceBefore=0)

def an_sec_header(num, title):
    label = f"{num}.  {title}" if num else title
    t = Table([[Paragraph(f"<b>{label}</b>", AN_S(10, bold=True, color=AN_WHITE))]], colWidths=[AN_TW])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),AN_RED),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),8),
    ]))
    return t

def an_empty_section(num, title, msg):
    return KeepTogether([an_sec_header(num, title),
        Table([[Paragraph(msg, AN_S(9, color=AN_GREY))]], colWidths=[AN_TW],
              style=[('LEFTPADDING',(0,0),(-1,-1),8),
                     ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]),
        Spacer(1, 2*mm)])

def an_data_table(headers, rows, col_widths):
    data = [[Paragraph(f"<b>{h}</b>", AN_S(9, bold=True, color=AN_WHITE, align=TA_CENTER)) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c or ''), AN_S(9, align=TA_CENTER)) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),AN_DARK),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[AN_WHITE,AN_LTRED]),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#DDDDDD')),
    ]))
    return t

def an_date_table(headers, rows, col_widths):
    data = [[Paragraph(f"<b>{h}</b>", AN_S(9, bold=True, color=AN_WHITE, align=TA_CENTER)) for h in headers]]
    keys = [k for k in rows[0].keys() if k not in ('dateFrom','dateTo','date')] if rows else []
    for row in rows:
        d_from = row.get('dateFrom','') or ''
        d_to   = row.get('dateTo','')   or ''
        if not d_from and not d_to:
            single = str(row.get('date','') or '')
            for sep in [' to ',' – ',' - ','–']:
                if sep in single:
                    parts = single.split(sep,1)
                    d_from = parts[0].strip(); d_to = parts[1].strip(); break
            else:
                d_from = single; d_to = ''
        date_text = f"{d_from}<br/>to {d_to}" if d_to else d_from
        date_cell = Paragraph(date_text, AN_S(9, align=TA_CENTER))
        rest = [Paragraph(str(row.get(k,'') or ''), AN_S(9)) for k in keys]
        data.append([date_cell] + rest)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),AN_DARK),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[AN_WHITE,AN_LTRED]),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#DDDDDD')),
    ]))
    return t

def an_bio_table(rows):
    CW = [38*mm, AN_TW/2-38*mm, 38*mm, AN_TW/2-38*mm]
    data = []; span_cmds = []
    for i, r in enumerate(rows):
        if len(r) == 4:
            data.append([Paragraph(f"<b>{r[0]}</b>", AN_S(10)),
                         Paragraph(str(r[1] or ''), AN_S(10)),
                         Paragraph(f"<b>{r[2]}</b>", AN_S(10)),
                         Paragraph(str(r[3] or ''), AN_S(10))])
        else:
            data.append([Paragraph(f"<b>{r[0]}</b>", AN_S(10)),
                         Paragraph(str(r[1] or ''), AN_S(10)),'',''])
            span_cmds.append(('SPAN',(1,i),(3,i)))
    style_cmds = [
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('LINEBELOW',(0,0),(-1,-2),0.3,colors.HexColor('#EEEEEE')),
        ('LINEABOVE',(0,8),(-1,8),1,colors.HexColor('#BBBBBB'),1,(3,3)),
    ] + span_cmds
    for i, r in enumerate(rows):
        style_cmds.append(('BACKGROUND',(0,i),(0,i),AN_LGREY))
        if len(r) == 4: style_cmds.append(('BACKGROUND',(2,i),(2,i),AN_LGREY))
    t = Table(data, colWidths=CW)
    t.setStyle(TableStyle(style_cmds))
    return t

def an_format_position(position, prof_level, specialty):
    pos_map = {"Doctor":"Physician"}
    position   = pos_map.get(position, position)
    prof_level = (prof_level or "").replace(" Doctor","").replace("Doctor ","").strip()
    return " — ".join([p for p in [position, prof_level, specialty] if p])

def build_an_pdf(data, redacted=False):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=AN_ML, rightMargin=AN_MR,
                            topMargin=AN_MT, bottomMargin=AN_MB)
    story = []
    pos_line = an_format_position(data.get('position',''), data.get('profLevel',''), data.get('specialty',''))

    # Logo
    logo_b64 = data.get('logoBase64','')
    if logo_b64:
        logo_elem = Image(io.BytesIO(base64.b64decode(logo_b64)), width=28*mm, height=28*mm)
    else:
        logo_elem = Table([["AL NAJAM\nLOGO"]], colWidths=[30*mm], rowHeights=[32*mm])
        logo_elem.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('FONTSIZE',(0,0),(-1,-1),7),('TEXTCOLOR',(0,0),(-1,-1),AN_GREY),
            ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#CCCCCC')),('BACKGROUND',(0,0),(-1,-1),AN_LGREY)]))

    # Photo
    photo_b64 = data.get('photoBase64','')
    if photo_b64:
        photo_elem = Image(io.BytesIO(base64.b64decode(photo_b64)), width=30*mm, height=38*mm)
    else:
        photo_elem = Table([["PHOTO"]], colWidths=[30*mm], rowHeights=[38*mm])
        photo_elem.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('FONTSIZE',(0,0),(-1,-1),9),('TEXTCOLOR',(0,0),(-1,-1),AN_GREY),
            ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#CCCCCC')),('BACKGROUND',(0,0),(-1,-1),AN_LGREY)]))

    title_content = [
        Paragraph("<b>RECRUITMENT APPLICATION FORM</b>", AN_S(15,bold=True,color=AN_RED,align=TA_CENTER)),
        Spacer(1,2*mm),
        Paragraph("Al Najam International — Human Resource Providers Since 1971 | License # 0899/LHR",
                  AN_S(8,color=AN_GOLD,align=TA_CENTER)),
        Spacer(1,3*mm),
        Paragraph(f"<b>Position:</b> {pos_line}", AN_S(10.5,align=TA_CENTER)),
    ]
    hdr = Table([[logo_elem, title_content, photo_elem]], colWidths=[32*mm, AN_TW-64*mm, 32*mm])
    hdr.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('LINEBELOW',(0,0),(-1,-1),2,AN_RED),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(hdr)
    story.append(Spacer(1,3*mm))

    # Key Skills
    skills = [s for s in (data.get('skills') or []) if s]
    if skills:
        story.append(KeepTogether([
            an_sec_header("","KEY SKILLS"),
            Table([[Paragraph("   •   ".join(skills), AN_S(10))]], colWidths=[AN_TW],
                  style=[('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
                         ('LEFTPADDING',(0,0),(-1,-1),8),('BACKGROUND',(0,0),(-1,-1),AN_LGREY)]),
            Spacer(1,2*mm)
        ]))

    # Bio
    bio_rows = [
        ("Full Name:",       data.get('fullName',''),       "Date of Birth:",       data.get('dob','')),
        ("CNIC:",            data.get('cnic',''),            "Gender:",              data.get('gender','')),
        ("Passport No:",     data.get('passportNo',''),      "Nationality:",         data.get('nationality','')),
        ("Passport Expiry:", data.get('passportExpiry',''),  "Religion:",            data.get('religion','')),
        ("Marital Status:",  data.get('maritalStatus',''),   "Dependents:",          data.get('dependents','')),
        ("Height:",          data.get('height',''),          "Weight:",              data.get('weight','')),
        ("GCC Experience:",  data.get('gccExp',''),          "English Proficiency:", data.get('english','')),
        ("Availability:",    data.get('availability',''),),
    ]
    if not redacted:
        bio_rows.append(("Email:", data.get('email',''), "Phone:", data.get('phone','')))
        bio_rows.append(("Address:", data.get('address',''),))
    story.append(KeepTogether([an_sec_header("1","BIOGRAPHICAL DATA"), an_bio_table(bio_rows), Spacer(1,2*mm)]))

    # Education
    quals = [q for q in (data.get('qualifications') or []) if q.get('degree') or q.get('institution')]
    if quals:
        rows = [{'dateFrom':q.get('dateFrom',''),'dateTo':q.get('dateTo',''),
                 'degree':q.get('degree',''),'institution':q.get('institution',''),'country':q.get('country','')} for q in quals]
        story.append(KeepTogether([an_sec_header("2","EDUCATION  (most recent first)"),
            an_date_table(["Date","Qualification / Degree","Institution","Country"],rows,[32*mm,58*mm,75*mm,25*mm]),
            Spacer(1,2*mm)]))
    else:
        story.append(an_empty_section("2","EDUCATION  (most recent first)","No education entries provided."))

    # Training
    trains = [t for t in (data.get('training') or []) if t.get('discipline') or t.get('institution')]
    if trains:
        rows = [{'dateFrom':t.get('dateFrom',''),'dateTo':t.get('dateTo',''),
                 'discipline':t.get('discipline',''),'institution':t.get('institution',''),'country':t.get('country','')} for t in trains]
        story.append(KeepTogether([an_sec_header("3","TRAINING / FELLOWSHIP"),
            an_date_table(["Date","Discipline / Specialty","Institution","Country"],rows,[32*mm,58*mm,75*mm,25*mm]),
            Spacer(1,2*mm)]))
    else:
        story.append(an_empty_section("3","TRAINING / FELLOWSHIP","No training entries provided."))

    # Licenses
    lics = [l for l in (data.get('licenses') or []) if l.get('licenseNo') or l.get('authority')]
    if lics:
        lic_rows = [[l.get('licenseNo',''),l.get('designation',''),
                     l.get('issueDate',''),l.get('expiryDate',''),l.get('authority','')] for l in lics]
        story.append(KeepTogether([an_sec_header("4","PROFESSIONAL LICENSES  (most recent first)"),
            an_data_table(["License No","Designation","Issue Date","Expiry","Authority"],
                          lic_rows,[28*mm,38*mm,26*mm,26*mm,72*mm]),
            Spacer(1,2*mm)]))
    else:
        story.append(an_empty_section("4","PROFESSIONAL LICENSES  (most recent first)","No licenses provided."))

    # Experience
    exps = [e for e in (data.get('experience') or []) if e.get('position') or e.get('institution')]
    if exps:
        rows = [{'dateFrom':e.get('dateFrom',''),'dateTo':e.get('dateTo',''),
                 'position':e.get('position',''),'institution':e.get('institution',''),'country':e.get('country','')} for e in exps]
        story.append(KeepTogether([an_sec_header("5","WORK EXPERIENCE  (most recent first)"),
            an_date_table(["Date","Position / Designation","Institution","Country"],rows,[32*mm,58*mm,75*mm,25*mm]),
            Spacer(1,2*mm)]))
    else:
        story.append(an_empty_section("5","WORK EXPERIENCE  (most recent first)","No experience entries provided."))

    # Footer
    story.append(HRFlowable(width=AN_TW, thickness=1, color=AN_GOLD, spaceAfter=2*mm))
    footer_txt = ("Al Najam International  |  License # 0899/LHR  |  Human Resource Providers Since 1971<br/>"
                  "+92 300 4747 115  |  support@alnajam.com  |  www.alnajam.com")
    if redacted:
        footer_txt += "<br/><font color='#C62D33'><b>[REDACTED — Contact details removed]</b></font>"
    story.append(Paragraph(footer_txt, AN_S(8,color=AN_GREY,align=TA_CENTER)))

    doc.build(story)
    buf.seek(0)
    return buf

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data     = request.get_json()
        redacted = data.get('redacted', False)
        pdf_buf  = build_an_pdf(data, redacted)
        suffix   = "Redacted" if redacted else "Full"
        parts    = [data.get('position',''), data.get('profLevel',''),
                    data.get('specialty',''), data.get('fullName','')]
        filename = " — ".join([p for p in parts if p]) + f" — {suffix}.pdf"
        return send_file(pdf_buf, mimetype='application/pdf',
                         as_attachment=True, download_name=filename)
    except Exception as e:
        print("GENERATE ERROR:", e)
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/generate_ngha', methods=['POST'])
def generate_ngha():
    """Generate NGHA/CRMS PDF and return bytes directly (no email)"""
    try:
        data = request.get_json()
        pdf  = build_pdf(data)
        name = data.get('candidate_name', 'Candidate').replace(' ', '_')
        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"NGHA_{name}.pdf"
        )
    except Exception as e:
        print("GENERATE_NGHA ERROR:", e)
        import traceback; traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health(): return jsonify({"status": "running", "services": ["cmrs", "alnajam-cv", "ngha"]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
