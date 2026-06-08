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

LOGO_B64 = "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"  # Fetched at runtime from Drive

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
            logo_img = Image(io.BytesIO(base64.b64decode(LOGO_B64)), width=18*mm, height=18*mm)
        except Exception as le:
            print('Logo error:', le)
            logo_img = Paragraph('', N)
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
    position   = pos_map.get(str(position or ''), str(position or ''))
    prof_level = str(prof_level or "").replace(" Doctor","").replace("Doctor ","").strip()
    specialty  = str(specialty or "")
    return " — ".join([p for p in [position, prof_level, specialty] if p])

def build_an_pdf(data, redacted=False):
    # Ensure all string fields are actually strings (sheet may send integers)
    for k in ['position','profLevel','specialty','fullName','cnic','passportNo',
              'passportExpiry','dob','gender','nationality','religion','maritalStatus',
              'dependents','height','weight','gccExp','english','availability',
              'email','phone','address','qualLevel','gradCountry']:
        if k in data: data[k] = str(data[k] or '')
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

    # Helper to safely convert to string
    def s(v): return str(v) if v is not None else ''

    # Bio
    bio_rows = [
        ("Full Name:",       s(data.get('fullName','')),       "Date of Birth:",       s(data.get('dob',''))),
        ("CNIC:",            s(data.get('cnic','')),            "Gender:",              s(data.get('gender',''))),
        ("Passport No:",     s(data.get('passportNo','')),      "Nationality:",         s(data.get('nationality',''))),
        ("Passport Expiry:", s(data.get('passportExpiry','')),  "Religion:",            s(data.get('religion',''))),
        ("Marital Status:",  s(data.get('maritalStatus','')),   "Dependents:",          s(data.get('dependents',''))),
        ("Height:",          s(data.get('height','')),          "Weight:",              s(data.get('weight',''))),
        ("GCC Experience:",  s(data.get('gccExp','')),          "English Proficiency:", s(data.get('english',''))),
        ("Availability:",    s(data.get('availability','')),),
    ]
    if not redacted:
        bio_rows.append(("Email:", s(data.get('email','')), "Phone:", s(data.get('phone',''))))
        bio_rows.append(("Address:", s(data.get('address','')),))
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
        parts    = [str(data.get('position','') or ''), str(data.get('profLevel','') or ''),
                    str(data.get('specialty','') or ''), str(data.get('fullName','') or '')]
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


# ═══════════════════════════════════════════════════════════════════════════
# NGHA NURSE / NON-CLINICAL APPLICATION FORM
# ═══════════════════════════════════════════════════════════════════════════

def build_ngha_ah_pdf(data):
    """Build exact replica of NGHA Non-Clinical Application Form (3 pages)"""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable, PageBreak, KeepTogether)
    from reportlab.platypus.flowables import Image as RLImage
    import base64

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=12*mm, rightMargin=12*mm,
                            topMargin=10*mm, bottomMargin=10*mm)

    W = A4[0] - 24*mm  # usable width

    # ── Styles ────────────────────────────────────────────────────────────────
    def S(size=9, bold=False, align=TA_LEFT, color=colors.black, italic=False):
        return ParagraphStyle('', fontSize=size, fontName='Helvetica-Bold' if bold else ('Helvetica-Oblique' if italic else 'Helvetica'),
                              leading=size*1.3, alignment=align, textColor=color)

    def P(text, size=9, bold=False, align=TA_LEFT, color=colors.black):
        return Paragraph(str(text or ''), S(size, bold, align, color))

    DARK_GREEN = colors.HexColor('#1a5276')
    LIGHT_GREY = colors.HexColor('#f2f2f2')
    MID_GREY   = colors.HexColor('#cccccc')
    BLACK      = colors.black
    WHITE      = colors.white

    def cell(text, size=9, bold=False, align=TA_LEFT, bg=None, span=False):
        return P(text, size, bold, align)

    def label_row(label, value='', label2='', value2=''):
        """Two-column label/value row"""
        c1 = P(f"<b>{label}</b>", 8)
        c2 = P(str(value), 8)
        if label2:
            c3 = P(f"<b>{label2}</b>", 8)
            c4 = P(str(value2), 8)
            return [c1, c2, c3, c4]
        return [c1, c2, '', '']

    def section_header(text):
        t = Table([[P(f"<b>{text}</b>", 9, bold=True, color=WHITE)]],
                  colWidths=[W])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), DARK_GREEN),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
        ]))
        return t

    def data_table(headers, rows, col_widths):
        """Standard data table with headers"""
        hdr = [P(f"<b>{h}</b>", 8, bold=True, align=TA_CENTER, color=WHITE) for h in headers]
        tdata = [hdr]
        for r in rows:
            tdata.append([P(str(c or ''), 8) for c in r])
        t = Table(tdata, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), DARK_GREEN),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
            ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        return t

    # ── Helper: safe string ───────────────────────────────────────────────────
    def s(v): return str(v) if v is not None and v != '' else ''

    # ── Data extraction ───────────────────────────────────────────────────────
    full_name   = s(data.get('fullName', ''))
    position    = s(data.get('position', ''))
    specialty   = s(data.get('specialty', ''))
    availability= s(data.get('availability', ''))
    gender      = s(data.get('gender', ''))
    religion    = s(data.get('religion', ''))
    nationality = s(data.get('nationality', ''))
    dob         = s(data.get('dob', ''))
    age         = s(data.get('age', ''))
    place_birth = s(data.get('placeOfBirth', ''))
    height      = s(data.get('height', ''))
    weight      = s(data.get('weight', ''))
    marital     = s(data.get('maritalStatus', ''))
    spouse_name = s(data.get('spouseName', ''))
    spouse_king = s(data.get('spouseInKingdom', ''))
    iqama       = s(data.get('iqamaNo', ''))
    sponsor     = s(data.get('companySponsor', ''))
    visa_type   = s(data.get('visaType', ''))
    emg_contact = s(data.get('emergencyName', ''))
    emg_mobile  = s(data.get('emergencyMobile', ''))
    employed    = s(data.get('currentlyEmployed', ''))
    date_left   = s(data.get('dateLeft', ''))
    app_date    = s(data.get('appDate', ''))
    locations   = data.get('nghaLocations', []) or []
    qualifications = data.get('qualifications', []) or []
    licenses    = data.get('licenses', []) or []
    training    = data.get('training', []) or []
    experience  = data.get('experience', []) or []
    references  = data.get('references', []) or []
    disclosure  = data.get('disclosure', []) or []

    # Al Najam constants
    AN_ADDRESS  = "Office 109, 1st Floor, Al Hafeez Executive, Ali Zeb Road, Gulberg 3, Lahore, Pakistan"
    AN_PHONE    = "+92 300 4747115"
    AN_EMAIL    = "support@alnajam.com"
    AN_NAME     = "Al Najam International"

    story = []

    # ═══════════════════════════════════════════════════════════════════════
    # PAGE 1 — INTERNATIONAL RECRUITMENT APPLICATION FORM
    # ═══════════════════════════════════════════════════════════════════════

    # ── Header ────────────────────────────────────────────────────────────
    ngha_b64 = data.get('nghaLogoBase64', '')
    if ngha_b64:
        try:
            logo = RLImage(io.BytesIO(base64.b64decode(ngha_b64)), width=20*mm, height=20*mm)
        except:
            logo = P('NGHA', 8, align=TA_CENTER)
    else:
        logo = P('NGHA', 8, align=TA_CENTER)

    hdr_left  = [P('Kingdom of Saudi Arabia', 8), P('Ministry of National Guard of Health Affairs', 8)]
    hdr_right = [P('المملكة العربية السعودية', 8, align=TA_RIGHT),
                 P('الشؤون الصحية بوزارة الحرس الوطني', 8, align=TA_RIGHT)]

    hdr_table = Table([[hdr_left, logo, hdr_right]], colWidths=[W*0.35, W*0.3, W*0.35])
    hdr_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'), ('ALIGN', (1,0), (1,0), 'CENTER'), ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(hdr_table)
    story.append(HRFlowable(width=W, thickness=1, color=DARK_GREEN, spaceAfter=2*mm))
    story.append(P('<b>International Recruitment Application Form</b>', 13, bold=True, align=TA_CENTER, color=DARK_GREEN))
    story.append(Spacer(1, 3*mm))

    # ── Date + Preferred Location + Position/Photo ────────────────────────
    loc_all = ['Riyadh', 'Jeddah', 'Madinah', 'Al Ahsa', 'Dammam', 'PHCs', 'No Preference']
    def loc_cell(loc):
        check = '☑' if loc in locations else '☐'
        return P(f"{check}  {loc}", 8)

    loc_grid = [[loc_cell(l) for l in loc_all[:4]],
                [loc_cell(l) for l in loc_all[4:]] + [''] * (4 - len(loc_all[4:]))]
    loc_table = Table(loc_grid, colWidths=[W*0.25]*4)
    loc_table.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))

    top_left = [
        [P('<b>Date of Application:</b>', 8), P(app_date or '____ / ____ / ________', 8)],
        [P('<b>Preferred location for employment</b>', 8, bold=True), ''],
    ]
    top_left_t = Table(top_left + [[loc_table, '']], colWidths=[W*0.55, W*0.1])
    top_left_t.setStyle(TableStyle([
        ('SPAN', (0,1), (1,1)), ('SPAN', (0,2), (1,2)),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
    ]))

    photo_box = Table([[P('Photo', 9, align=TA_CENTER, color=colors.grey)]], colWidths=[28*mm], rowHeights=[35*mm])
    photo_box.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, MID_GREY),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    pos_box = Table([
        [P('<b>Position you are applying for:</b>', 8), P(position, 8)],
        [P('<b>Area of Speciality:</b>', 8), P(specialty, 8)],
        [P('<b>Availability:</b>', 8), P(availability, 8)],
    ], colWidths=[W*0.3, W*0.35])
    pos_box.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    top_right = Table([[pos_box], [photo_box]], colWidths=[W*0.35])
    outer_top = Table([[top_left_t, top_right]], colWidths=[W*0.65, W*0.35])
    outer_top.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(outer_top)
    story.append(Spacer(1, 2*mm))

    # ── Recruitment Source ────────────────────────────────────────────────
    rec_src = Table([
        [P('<b>Recruitment Source:</b>', 8), P('☑  Agency', 8), P('☐  Internet', 8), P('☐  Local', 8)],
        ['', P('☐  Referred', 8), P('☐  Rehire', 8), P('☐  Other', 8)],
    ], colWidths=[W*0.25, W*0.25, W*0.25, W*0.25])
    rec_src.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))

    ref_box = Table([
        [P('<b>Referred by (Name & Badge No.):</b>', 8), P('N/A', 8)],
    ], colWidths=[W*0.5, W*0.5])
    ref_box.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))

    src_row = Table([[rec_src, ref_box]], colWidths=[W*0.5, W*0.5])
    story.append(src_row)
    story.append(Spacer(1, 2*mm))

    # ── Personal Data ─────────────────────────────────────────────────────
    story.append(section_header('Personal Data: (Please print clearly)'))
    story.append(Spacer(1, 1*mm))

    # Split full name into first/family
    name_parts = full_name.split(' ')
    first_name  = name_parts[0] if name_parts else ''
    family_name = name_parts[-1] if len(name_parts) > 1 else ''

    personal_data = [
        [P('<b>First Name:</b>', 8), P(first_name, 8), P('<b>Permanent Address:</b>', 8), P(AN_ADDRESS, 7)],
        [P('<b>Second Name:</b>', 8), P('', 8), '', ''],
        [P('<b>Family Name:</b>', 8), P(family_name, 8), P('<b>Telephone No.:</b>', 8), P(AN_PHONE, 8)],
        [P('<b>Gender:</b>', 8), P(gender, 8), P('<b>Mobile No.:</b>', 8), P(AN_PHONE, 8)],
        [P('<b>Nationality:</b>', 8), P(nationality, 8), P('<b>Current Address:</b>', 8), P('<i>(No need to fill if same as permanent)</i>', 7, color=colors.grey)],
        [P('<b>Date of Birth (DD-MM-YYYY):</b>', 8), P(dob, 8), P('', 8), P('', 8)],
        [P('<b>Place of Birth (include Country):</b>', 8), P(place_birth, 8), P('<b>Telephone No./Mobile No.:</b>', 8), P(AN_PHONE, 8)],
        [P('<b>Height (in cm):</b>', 8), P(height, 8), P('<b>Weight (in kgs.):</b>', 8), P(weight, 8)],
        [P('<b>Marital Status:</b>', 8), P(marital, 8), P('<b>Email Address:</b>', 8), P(AN_EMAIL, 8)],
        [P('<b>Name of Spouse:</b>', 8), P(spouse_name, 7), '', ''],
    ]

    pd_table = Table(personal_data, colWidths=[W*0.28, W*0.22, W*0.28, W*0.22])
    pd_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('SPAN', (2,0), (3,0)), ('SPAN', (2,1), (3,1)),
        ('SPAN', (2,8), (3,8)),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,0), (0,-1), LIGHT_GREY), ('BACKGROUND', (2,0), (2,-1), LIGHT_GREY),
        ('VALIGN', (2,0), (3,0), 'TOP'),
    ]))
    story.append(pd_table)

    # Spouse/Iqama row
    spouse_row = Table([
        [P('<b>Is your Spouse living in the Kingdom?</b>', 8),
         P(f"{'☑' if spouse_king=='Yes' else '☐'}  Yes    {'☑' if spouse_king=='No' else '☐'}  No", 8),
         P('<b>Company/Sponsor:</b>', 8), P(sponsor, 8)],
        [P('<b>Iqama/Residency Permit No.:</b>', 8), P(iqama, 8),
         P('<b>Visa Type:</b>', 8),
         P(f"{'☑' if visa_type=='Work' else '☐'}  Work    {'☑' if visa_type=='Dependent' else '☐'}  Dependent    {'☑' if visa_type=='Visit' else '☐'}  Visit", 8)],
        [P('<b>Emergency Contact Person:</b>', 8), P(emg_contact, 8),
         P('<b>Mobile No.:</b>', 8), P(emg_mobile, 8)],
    ], colWidths=[W*0.28, W*0.22, W*0.28, W*0.22])
    spouse_row.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,0), (0,-1), LIGHT_GREY), ('BACKGROUND', (2,0), (2,-1), LIGHT_GREY),
    ]))
    story.append(spouse_row)
    story.append(Spacer(1, 2*mm))

    # ── Qualifications ────────────────────────────────────────────────────
    story.append(section_header('Qualifications: (Please attach copies of all qualifications listed below)'))
    story.append(Spacer(1, 1*mm))
    qual_rows = []
    for q in qualifications[:4]:
        qual_rows.append([
            s(q.get('institution', '')), s(q.get('country', '')),
            s(q.get('dateFrom', '')), s(q.get('dateTo', '')), s(q.get('degree', ''))
        ])
    while len(qual_rows) < 4:
        qual_rows.append(['', '', '', '', ''])
    story.append(data_table(
        ['Name of College/University', 'Country', 'From', 'To', 'Qualification Gained'],
        qual_rows,
        [W*0.35, W*0.15, W*0.15, W*0.15, W*0.2]
    ))
    story.append(Spacer(1, 2*mm))

    # ── Professional Licensing ────────────────────────────────────────────
    lic_rows = []
    for l in licenses[:3]:
        lic_rows.append([s(l.get('authority', '')), s(l.get('country', '')),
                         s(l.get('licenseNo', '')), s(l.get('expiryDate', ''))])
    while len(lic_rows) < 3:
        lic_rows.append(['', '', '', ''])
    story.append(data_table(
        ['Professional Licensing Body', 'Country', 'License/Registration No.', 'Expiration Date'],
        lic_rows, [W*0.35, W*0.15, W*0.3, W*0.2]
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # PAGE 2
    # ═══════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    # ── Trainings ─────────────────────────────────────────────────────────
    train_rows = []
    for t in training[:4]:
        train_rows.append([s(t.get('discipline', '')),
                           s(t.get('dateFrom', '')), s(t.get('courseTitle', ''))])
    while len(train_rows) < 4:
        train_rows.append(['', '', ''])
    story.append(data_table(
        ['Trainings Attended', 'Date Attended', 'Course Title'],
        train_rows, [W*0.45, W*0.2, W*0.35]
    ))
    story.append(Spacer(1, 2*mm))

    # ── Employment History ────────────────────────────────────────────────
    story.append(section_header('Employment History: (Start from current or most recent employment and attach a detailed CV/resume supporting this)'))
    story.append(Spacer(1, 1*mm))
    exp_rows = []
    for e in experience[:5]:
        exp_rows.append([
            s(e.get('institution', '')),
            s(e.get('dateFrom', '')), s(e.get('dateTo', '')),
            s(e.get('position', '')), s(e.get('wardUnit', ''))
        ])
    while len(exp_rows) < 5:
        exp_rows.append(['', '', '', '', ''])
    story.append(data_table(
        ['Hospital/Company/Employer Name & Address', 'From', 'To', 'Last Position Held/Job Title', 'Ward/Unit/Department'],
        exp_rows, [W*0.35, W*0.12, W*0.12, W*0.22, W*0.19]
    ))
    story.append(Spacer(1, 2*mm))

    # Employment status row
    emp_status = Table([
        [P('<b>Last Date of Employment:</b>', 8), P(date_left, 8), '', ''],
        [P('<b>Are you currently employed?</b>', 8),
         P(f"{'☑' if employed=='Yes' else '☐'}  Yes    {'☑' if employed=='No' else '☐'}  No", 8),
         P('<b>Date left (last employment):</b>', 8), P(date_left, 8)],
    ], colWidths=[W*0.3, W*0.2, W*0.3, W*0.2])
    emp_status.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('SPAN', (1,0), (3,0)),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,0), (0,-1), LIGHT_GREY), ('BACKGROUND', (2,1), (2,1), LIGHT_GREY),
    ]))
    story.append(emp_status)
    story.append(Spacer(1, 2*mm))

    # ── Work References ───────────────────────────────────────────────────
    story.append(section_header('Work Related Reference who may be contacted:'))
    story.append(Spacer(1, 1*mm))

    ref_data = [
        [P('<b>Name</b>', 8, bold=True, align=TA_CENTER, color=WHITE),
         P('<b>Position/Job Title</b>', 8, bold=True, align=TA_CENTER, color=WHITE),
         P('<b>Contact Information</b>', 8, bold=True, align=TA_CENTER, color=WHITE),
         P('<b>Consent to Contact</b>', 8, bold=True, align=TA_CENTER, color=WHITE)],
    ]
    for i, ref in enumerate(references[:2]):
        name = s(ref.get('name', ''))
        title = s(ref.get('jobTitle', ''))
        work = s(ref.get('work', ''))
        email = s(ref.get('email', ''))
        consent = s(ref.get('consent', ''))
        contact_text = f"Work: {work}\nEmail: {email}"
        consent_text = '☑  Yes' if consent == 'Yes' else '☑  No — will not be contacted until consent is sought'
        ref_data.append([P(name, 8), P(title, 8), P(contact_text, 8), P(consent_text, 8)])

    while len(ref_data) < 3:
        ref_data.append([P('', 8), P('', 8), P('', 8), P('', 8)])

    ref_table = Table(ref_data, colWidths=[W*0.2, W*0.2, W*0.35, W*0.25])
    ref_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), DARK_GREEN),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(ref_table)
    story.append(Spacer(1, 3*mm))

    # ── Authorization ─────────────────────────────────────────────────────
    auth_text = (
        "I hereby authorize the Recruitment Services of Ministry of National Guard Health Affairs to request and obtain "
        "details held about me from any organization, in order to exercise due diligence verifying the documents and "
        "details I have submitted to its office in support of my educational qualifications and experience.\n\n"
        "I understand that these organizations can include academic institutions, professional medical bodies, licensing "
        "and registration bodies and my current and previous employers, including referees.\n\n"
        "Furthermore, I declare that all the information that I have given above is correct to the best of my knowledge. "
        "I understand that I could have my contract terminated (or my offer of employment cancelled); if it is found that "
        "I have deliberately given false or misleading information or if my professional license is revoked during or "
        "after the application process."
    )
    story.append(P('<b>Authorization</b>', 9, bold=True, align=TA_CENTER))
    story.append(Spacer(1, 2*mm))
    story.append(P(auth_text, 8))
    story.append(Spacer(1, 4*mm))

    # Signature row
    sig_table = Table([
        [P('<b>Signature of Applicant:</b>', 8), P('', 8), P('<b>Date:</b>', 8), P('', 8)],
    ], colWidths=[W*0.35, W*0.15, W*0.2, W*0.3])
    sig_table.setStyle(TableStyle([
        ('LINEBELOW', (1,0), (1,0), 0.5, BLACK), ('LINEBELOW', (3,0), (3,0), 0.5, BLACK),
        ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 3*mm))

    # Source verification statement
    story.append(P('As an essential function and responsibility of a recruitment agency, I confirm that primary source verification of the above applicant\'s license, qualification & experience will be implemented when offer released.', 8))
    story.append(Spacer(1, 3*mm))

    # ── Recruitment Agency Info ───────────────────────────────────────────
    agency_table = Table([
        [P('<b>Recruitment Agency Information: (If applicable)</b>', 8, bold=True), '', '', ''],
        [P('<b>Name of Recruitment Agency:</b>', 8), P(AN_NAME, 8), '', ''],
        [P('<b>Recruiter Name:</b>', 8), P(AN_NAME, 8), P('<b>Email:</b>', 8), P(AN_EMAIL, 8)],
        [P('<b>Agency Signature:</b>', 8), P('', 8), P('<b>Date:</b>', 8), P(app_date or '', 8)],
    ], colWidths=[W*0.28, W*0.22, W*0.28, W*0.22])
    agency_table.setStyle(TableStyle([
        ('SPAN', (0,0), (3,0)), ('SPAN', (1,1), (3,1)),
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('BACKGROUND', (0,0), (-1,0), LIGHT_GREY),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(agency_table)

    # Page footer
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width=W, thickness=0.5, color=MID_GREY))
    story.append(P('Non-Clinical Form    Rev. 12/2023    Ref# APP 1423-02, Appendix D    Page 1 of 2    APP 1427-18, Appendix C    CPRA # 0601-1158', 7, align=TA_CENTER, color=colors.grey))

    # ═══════════════════════════════════════════════════════════════════════
    # PAGE 3 — DISCLOSURE FORM FOR NEW APPLICANTS
    # ═══════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    # Disclosure header
    story.append(P('<b>Kingdom of Saudi Arabia</b>', 9, bold=True))
    story.append(P('Ministry of National Guard Health Affairs', 8))
    story.append(Spacer(1, 3*mm))
    story.append(P('<b>Disclosure Form For New Applicants</b>', 12, bold=True, align=TA_CENTER, color=DARK_GREEN))
    story.append(HRFlowable(width=W, thickness=1, color=DARK_GREEN, spaceAfter=2*mm))
    story.append(P('<b>Part I</b> - To be completed by the Applicant', 9, bold=True, align=TA_CENTER))
    story.append(Spacer(1, 3*mm))

    disc_header = Table([
        [P('<b>Position Applied For:</b>', 8), P(position, 8),
         P('<b>Gender:</b>', 8),
         P(f"{'☑' if gender=='Male' else '☐'}  Male    {'☑' if gender=='Female' else '☐'}  Female", 8)],
        [P('<b>Nationality:</b>', 8), P(nationality, 8), '', ''],
        [P('<b>Postal Address:</b>', 8), P(AN_ADDRESS, 7), '', ''],
        [P('<b>Phone No. Including Country Code:</b>', 8), P(AN_PHONE, 8),
         P('<b>E-mail:</b>', 8), P(AN_EMAIL, 8)],
    ], colWidths=[W*0.28, W*0.22, W*0.28, W*0.22])
    disc_header.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, MID_GREY),
        ('SPAN', (1,1), (3,1)), ('SPAN', (1,2), (3,2)),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,0), (0,-1), LIGHT_GREY), ('BACKGROUND', (2,0), (2,0), LIGHT_GREY),
        ('BACKGROUND', (2,3), (2,3), LIGHT_GREY),
        ('VALIGN', (1,2), (1,2), 'TOP'),
    ]))
    story.append(disc_header)
    story.append(Spacer(1, 3*mm))

    story.append(P('I disclose herewith all my relationships and affiliations with those currently employed in all Ministry of National Guard Health Affairs facilities*.', 8))
    story.append(Spacer(1, 2*mm))
    story.append(P('<b>Relatives / Acquaintances working for Ministry of National Guard Health Affairs:</b>', 8, bold=True))
    story.append(Spacer(1, 2*mm))

    disc_rows = []
    for i in range(5):
        d = disclosure[i] if i < len(disclosure) else {}
        disc_rows.append([
            P(str(i+1), 8, align=TA_CENTER),
            P(s(d.get('name', '')), 8),
            P(s(d.get('position', '')), 8),
            P(s(d.get('department', '')), 8),
            P(s(d.get('relationship', '')), 8),
        ])
    story.append(data_table(
        ['#', 'Name', 'Position', 'Department', 'Relationship To Applicant'],
        disc_rows, [W*0.06, W*0.25, W*0.23, W*0.23, W*0.23]
    ))
    story.append(Spacer(1, 3*mm))

    story.append(P('I hereby certify that the above information is true and complete to the best of my knowledge and belief.', 8))
    story.append(Spacer(1, 6*mm))

    cert_table = Table([
        ['', P('', 8), P('N/A', 8), P(app_date or '', 8)],
        ['', P('<b>Name & Signature</b>', 8, bold=True, align=TA_CENTER), P('<b>Badge No.</b>', 8, bold=True, align=TA_CENTER), P('<b>Date</b>', 8, bold=True, align=TA_CENTER)],
    ], colWidths=[W*0.1, W*0.4, W*0.25, W*0.25])
    cert_table.setStyle(TableStyle([
        ('LINEABOVE', (1,0), (1,0), 0.5, BLACK),
        ('LINEABOVE', (2,0), (2,0), 0.5, BLACK),
        ('LINEABOVE', (3,0), (3,0), 0.5, BLACK),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(cert_table)
    story.append(Spacer(1, 2*mm))
    story.append(P('<i>* <b>Note:</b> Non-disclosure may result in rejection of application.</i>', 8))
    story.append(Spacer(1, 4*mm))

    story.append(HRFlowable(width=W, thickness=0.5, color=MID_GREY))
    story.append(Spacer(1, 2*mm))
    story.append(P('<b>Part II</b> - To be completed by the Recruitment Agency or appropriate Recruitment Services', 9, bold=True, align=TA_CENTER))
    story.append(Spacer(1, 4*mm))
    story.append(P('<b>Verified by:</b>', 9, bold=True))
    story.append(Spacer(1, 6*mm))

    verified_table = Table([
        ['', P('', 8), P('N/A', 8), P(app_date or '', 8)],
        ['', P('<b>Name & Signature</b>', 8, bold=True, align=TA_CENTER), P('<b>Badge/ID No.</b>', 8, bold=True, align=TA_CENTER), P('<b>Date</b>', 8, bold=True, align=TA_CENTER)],
    ], colWidths=[W*0.1, W*0.4, W*0.25, W*0.25])
    verified_table.setStyle(TableStyle([
        ('LINEABOVE', (1,0), (1,0), 0.5, BLACK),
        ('LINEABOVE', (2,0), (2,0), 0.5, BLACK),
        ('LINEABOVE', (3,0), (3,0), 0.5, BLACK),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(verified_table)
    story.append(Spacer(1, 4*mm))

    # Stamp box
    stamp_table = Table([[P('Recruitment Stamp', 9, align=TA_CENTER, color=colors.grey)]], colWidths=[40*mm], rowHeights=[40*mm])
    stamp_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, MID_GREY),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(stamp_table)
    story.append(Spacer(1, 3*mm))

    story.append(HRFlowable(width=W, thickness=0.5, color=MID_GREY))
    story.append(P('Non-Clinical Form    Rev. 08/2022    Ref# APP 1427-18, Appendix A    Page 1 of 1    APP 1443-11, Appendix A    CPRA # 0503-0140', 7, align=TA_CENTER, color=colors.grey))

    doc.build(story)
    buf.seek(0)
    return buf


@app.route('/generate_ngha_ah', methods=['POST'])
def generate_ngha_ah():
    """Generate NGHA Non-Clinical (Nurse/Allied Health) Application Form PDF"""
    try:
        data = request.get_json()
        pdf_buf = build_ngha_ah_pdf(data)
        name_parts = [str(data.get('position','') or ''), str(data.get('fullName','') or '')]
        filename = "NGHA Allied Health Form — " + " — ".join([p for p in name_parts if p]) + ".pdf"
        return send_file(pdf_buf, mimetype='application/pdf',
                         as_attachment=True, download_name=filename)
    except Exception as e:
        print("NGHA NURSE ERROR:", e)
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500
