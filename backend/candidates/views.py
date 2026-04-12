import io
import zipfile
from datetime import date, datetime
import openpyxl
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from .models import Candidate
from .serializers import CandidateSerializer


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _rupees(amount):
    try:
        return f"Rs. {int(float(amount)):,} per annum"
    except Exception:
        return str(amount)


def _fmt_date(d):
    if isinstance(d, datetime):
        return d.strftime("%d %B %Y")
    if isinstance(d, date):
        return d.strftime("%d %B %Y")
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        return str(d) if d else "To be confirmed"


def _read_excel(excel_file):
    """Return (headers list, candidates list-of-dicts) or raise ValueError."""
    try:
        wb = openpyxl.load_workbook(excel_file, data_only=True)
    except Exception as e:
        raise ValueError(f"Could not read Excel file: {e}")

    ws   = wb.active
    rows = list(ws.iter_rows(values_only=True))

    if not rows or not rows[0]:
        raise ValueError("Excel file is empty.")

    headers = [
        str(c).strip().lower().replace(" ", "_") if c is not None else ""
        for c in rows[0]
    ]

    candidates = []
    for row in rows[1:]:
        if all(v is None for v in row):
            continue
        candidates.append(dict(zip(headers, row)))

    if not candidates:
        raise ValueError("No candidate data found in Excel.")

    return headers, candidates


def _make_response(candidates, generate_fn, single_name_prefix, zip_name):
    """Generate PDF(s) and return HttpResponse."""
    if len(candidates) == 1:
        pdf_bytes = generate_fn(candidates[0])
        safe      = str(candidates[0].get("name", "candidate")).replace(" ", "_")
        response  = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{single_name_prefix}_{safe}.pdf"'
        )
        response["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, c in enumerate(candidates, 1):
            pdf_bytes = generate_fn(c)
            safe      = str(c.get("name", f"candidate_{i}")).replace(" ", "_")
            zf.writestr(f"{single_name_prefix}_{safe}.pdf", pdf_bytes)

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{zip_name}"'
    response["Access-Control-Expose-Headers"] = "Content-Disposition"
    return response


# ══════════════════════════════════════════════════════════════════════════════
#  OFFER LETTER
# ══════════════════════════════════════════════════════════════════════════════

def generate_offer_letter_pdf(candidate_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm,     bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    company_style = ParagraphStyle(
        "CompanyName", parent=styles["Normal"],
        fontSize=20, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a237e"), spaceAfter=6,
    )
    tagline_style = ParagraphStyle(
        "Tagline", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica",
        textColor=colors.HexColor("#5c6bc0"),
        spaceBefore=0, spaceAfter=10,
    )
    date_style = ParagraphStyle(
        "Date", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", alignment=2,
    )
    heading_style = ParagraphStyle(
        "OfferHeading", parent=styles["Normal"],
        fontSize=15, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a237e"),
        spaceBefore=10, spaceAfter=6, alignment=1,
    )
    subheading_style = ParagraphStyle(
        "SubHeading", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#283593"),
        spaceBefore=12, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", leading=16, spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica",
        textColor=colors.grey, alignment=1,
    )

    today_str = date.today().strftime("%d %B %Y")
    name      = str(candidate_data.get("name")     or "Candidate").strip()
    role      = str(candidate_data.get("role")     or "Associate").strip()
    email     = str(candidate_data.get("email")    or "").strip()
    phone     = str(candidate_data.get("phone")    or "").strip()
    loc       = str(candidate_data.get("location") or "Chennai, Tamil Nadu").strip()
    prev_co   = str(candidate_data.get("previous_company") or "").strip()
    cur_sal   = _rupees(candidate_data.get("current_salary")  or 0)
    ctc       = _rupees(candidate_data.get("offered_ctc")     or
                        candidate_data.get("expected_salary") or 0)
    joining   = _fmt_date(candidate_data.get("joining_date"))

    story = []
    story.append(Paragraph("Bit Byte Technologies.", company_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Empowering Talent  |  Building Tomorrow", tagline_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Date: {today_str}", date_style))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#1a237e"), spaceAfter=10))
    story.append(Paragraph("OFFER OF EMPLOYMENT", heading_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Dear <b>{name}</b>,", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"We are delighted to extend this offer of employment to you for the position of "
        f"<b>{role}</b> at <b>Bit Byte Technologies.</b>, located at <b>{loc}</b>. "
        f"This offer is subject to the terms and conditions mentioned below.",
        body_style,
    ))

    story.append(Paragraph("Candidate Details", subheading_style))
    details = [
        ["Full Name",        name],
        ["Email Address",    email   or "—"],
        ["Phone Number",     phone   or "—"],
        ["Designation",      role],
        ["Previous Company", prev_co or "—"],
        ["Work Location",    loc],
        ["Date of Joining",  joining],
    ]
    tbl = Table(details, colWidths=[5.5*cm, 10.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eaf6")),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",   (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#9fa8da")),
        ("PADDING",    (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#f5f5f5"), colors.white]),
    ]))
    story.append(tbl)

    story.append(Paragraph("Compensation & Benefits", subheading_style))
    story.append(Paragraph(
        f"We are pleased to offer you a Cost to Company (CTC) of <b>{ctc}</b>. "
        f"The detailed break-up of your compensation will be shared separately.",
        body_style,
    ))
    comp_rows = [
        ["Component",        "Details"],
        ["Annual CTC",       ctc],
        ["Current CTC",      cur_sal],
        ["Pay Cycle",        "Monthly"],
        ["Probation Period", "6 Months"],
        ["Notice Period",    "60 Days (post-probation)"],
    ]
    comp_tbl = Table(comp_rows, colWidths=[6*cm, 10*cm])
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#9fa8da")),
        ("PADDING",     (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f5f5f5"), colors.white]),
    ]))
    story.append(comp_tbl)

    story.append(Paragraph("Terms & Conditions", subheading_style))
    for i, cond in enumerate([
        "This offer is contingent upon successful completion of background verification.",
        "You are required to submit all original educational certificates on your date of joining.",
        "Resignation from your current employer and serving the required notice period is mandatory.",
        "This offer is strictly confidential and non-transferable.",
        "Bit Byte Technologies reserves the right to withdraw this offer if any information provided is found to be false.",
    ], 1):
        story.append(Paragraph(f"{i}. {cond}", body_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Please sign and return a copy of this letter as your acceptance within "
        "<b>7 days</b> from the date of this letter. We look forward to welcoming you!",
        body_style,
    ))
    story.append(Spacer(1, 24))
    sig_data = [
        ["Authorised Signatory",        "", "Candidate Acceptance"],
        ["Bit Byte Technologies.",       "", name],
        ["", "", ""],
        ["_______________________",     "", "_______________________"],
        ["HR Manager",                  "", "Date: ____________________"],
    ]
    sig_tbl = Table(sig_data, colWidths=[7*cm, 2*cm, 7*cm])
    sig_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("VALIGN",   (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",  (0, 0), (-1, -1), 3),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#9fa8da")))
    story.append(Paragraph(
        "Bit Byte Technologies.  |  Chennai, Tamil Nadu  |  hr@bitbyte.com  |  +91 44 0000 0000",
        footer_style,
    ))

    doc.build(story)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
#  APPOINTMENT LETTER
# ══════════════════════════════════════════════════════════════════════════════

def generate_appointment_letter_pdf(candidate_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm,     bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    # ── Styles (green theme for appointment) ──────────────────────────────────
    DARK_GREEN  = colors.HexColor("#1b5e20")
    MID_GREEN   = colors.HexColor("#2e7d32")
    LIGHT_GREEN = colors.HexColor("#e8f5e9")
    LINE_GREEN  = colors.HexColor("#81c784")

    company_style = ParagraphStyle(
        "CompanyName", parent=styles["Normal"],
        fontSize=20, fontName="Helvetica-Bold",
        textColor=DARK_GREEN, spaceAfter=6,
    )
    tagline_style = ParagraphStyle(
        "Tagline", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica",
        textColor=MID_GREEN, spaceBefore=0, spaceAfter=10,
    )
    date_style = ParagraphStyle(
        "Date", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", alignment=2,
    )
    heading_style = ParagraphStyle(
        "ApptHeading", parent=styles["Normal"],
        fontSize=15, fontName="Helvetica-Bold",
        textColor=DARK_GREEN, spaceBefore=10, spaceAfter=6, alignment=1,
    )
    subheading_style = ParagraphStyle(
        "SubHeading", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Bold",
        textColor=DARK_GREEN, spaceBefore=12, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", leading=16, spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica",
        textColor=colors.grey, alignment=1,
    )

    today_str   = date.today().strftime("%d %B %Y")
    name        = str(candidate_data.get("name")        or "Employee").strip()
    role        = str(candidate_data.get("role")        or "Associate").strip()
    email       = str(candidate_data.get("email")       or "").strip()
    phone       = str(candidate_data.get("phone")       or "").strip()
    loc         = str(candidate_data.get("location")    or "Chennai, Tamil Nadu").strip()
    dept        = str(candidate_data.get("department")  or "Technology").strip()
    emp_id      = str(candidate_data.get("employee_id") or "—").strip()
    ctc         = _rupees(candidate_data.get("offered_ctc") or
                          candidate_data.get("expected_salary") or 0)
    joining     = _fmt_date(candidate_data.get("joining_date"))

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Bit Byte Technologies.", company_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Empowering Talent  |  Building Tomorrow", tagline_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Date: {today_str}", date_style))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK_GREEN, spaceAfter=10))

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("APPOINTMENT LETTER", heading_style))
    story.append(Spacer(1, 4))

    # ── Reference line ────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"<b>Ref No:</b> BBT/HR/{date.today().year}/{emp_id}",
        body_style,
    ))
    story.append(Paragraph(f"<b>To,</b>", body_style))
    story.append(Paragraph(f"<b>{name}</b>", body_style))
    story.append(Spacer(1, 6))

    # ── Opening paragraph ─────────────────────────────────────────────────────
    story.append(Paragraph(
        f"With reference to your application and subsequent interview, we are pleased to appoint you as "
        f"<b>{role}</b> in the <b>{dept}</b> department at <b>Bit Byte Technologies.</b>, "
        f"located at <b>{loc}</b>, with effect from <b>{joining}</b>.",
        body_style,
    ))

    # ── Employee details table ─────────────────────────────────────────────────
    story.append(Paragraph("Employee Details", subheading_style))
    details = [
        ["Employee Name",   name],
        ["Employee ID",     emp_id],
        ["Designation",     role],
        ["Department",      dept],
        ["Email Address",   email   or "—"],
        ["Phone Number",    phone   or "—"],
        ["Work Location",   loc],
        ["Date of Joining", joining],
    ]
    tbl = Table(details, colWidths=[5.5*cm, 10.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREEN),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",   (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("GRID",       (0, 0), (-1, -1), 0.5, LINE_GREEN),
        ("PADDING",    (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [LIGHT_GREEN, colors.white]),
    ]))
    story.append(tbl)

    # ── Compensation table ────────────────────────────────────────────────────
    story.append(Paragraph("Compensation & Benefits", subheading_style))
    story.append(Paragraph(
        f"Your annual Cost to Company (CTC) will be <b>{ctc}</b>, "
        f"payable monthly. A detailed salary break-up will be provided separately.",
        body_style,
    ))
    comp_rows = [
        ["Component",           "Details"],
        ["Annual CTC",          ctc],
        ["Pay Cycle",           "Monthly"],
        ["Probation Period",    "3 Months"],
        ["Notice Period",       "30 Days (probation) / 60 Days (confirmed)"],
        ["Working Hours",       "9:00 AM – 6:00 PM (Mon–Fri)"],
        ["Annual Leave",        "18 Days per year"],
    ]
    comp_tbl = Table(comp_rows, colWidths=[6*cm, 10*cm])
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), DARK_GREEN),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("GRID",        (0, 0), (-1, -1), 0.5, LINE_GREEN),
        ("PADDING",     (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [LIGHT_GREEN, colors.white]),
    ]))
    story.append(comp_tbl)

    # ── Terms ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("Terms & Conditions of Employment", subheading_style))
    terms = [
        "Your appointment is subject to satisfactory completion of your probation period of 3 months.",
        "You shall devote your full working time and attention to the duties assigned to you.",
        "You are required to maintain strict confidentiality of all company information.",
        "You shall not take up any other employment, business, or consultancy during your service.",
        "Any misconduct or breach of company policy may lead to immediate termination.",
        "This appointment letter supersedes all prior communications related to this employment.",
    ]
    for i, term in enumerate(terms, 1):
        story.append(Paragraph(f"{i}. {term}", body_style))

    # ── Closing ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "We welcome you to the Bit Byte Technologies family and look forward to a long and "
        "mutually rewarding association. Please sign the duplicate copy of this letter as your "
        "acceptance and return it to the HR department on or before your date of joining.",
        body_style,
    ))

    # ── Signature block ───────────────────────────────────────────────────────
    story.append(Spacer(1, 24))
    sig_data = [
        ["For Bit Byte Technologies.",   "", "Accepted by"],
        ["",                             "", name],
        ["",                             "", ""],
        ["_______________________",      "", "_______________________"],
        ["Authorised Signatory / HR",    "", f"Date: ____________________"],
    ]
    sig_tbl = Table(sig_data, colWidths=[7*cm, 2*cm, 7*cm])
    sig_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("VALIGN",   (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",  (0, 0), (-1, -1), 3),
    ]))
    story.append(sig_tbl)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE_GREEN))
    story.append(Paragraph(
        "Bit Byte Technologies.  |  Chennai, Tamil Nadu  |  hr@bitbyte.com  |  +91 44 0000 0000",
        footer_style,
    ))

    doc.build(story)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
#  API VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_excel_generate_pdf(request):
    """POST /api/generate-offer-letters/"""
    if "file" not in request.FILES:
        return Response({"error": "No file uploaded. Use key 'file'."}, status=400)
    try:
        _, candidates = _read_excel(request.FILES["file"])
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    required = {"name", "role"}
    missing  = required - set(candidates[0].keys())
    if missing:
        return Response({"error": f"Missing columns: {missing}"}, status=400)

    return _make_response(candidates, generate_offer_letter_pdf,
                          "offer_letter", "offer_letters.zip")


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_excel_generate_appointment_pdf(request):
    """POST /api/generate-appointment-letters/"""
    if "file" not in request.FILES:
        return Response({"error": "No file uploaded. Use key 'file'."}, status=400)
    try:
        _, candidates = _read_excel(request.FILES["file"])
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    required = {"name", "role"}
    missing  = required - set(candidates[0].keys())
    if missing:
        return Response({"error": f"Missing columns: {missing}"}, status=400)

    return _make_response(candidates, generate_appointment_letter_pdf,
                          "appointment_letter", "appointment_letters.zip")


# ══════════════════════════════════════════════════════════════════════════════
#  JOINING LETTER
# ══════════════════════════════════════════════════════════════════════════════

def generate_joining_letter_pdf(candidate_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm,     bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    DARK_ORG  = colors.HexColor("#bf360c")
    MID_ORG   = colors.HexColor("#e64a19")
    LIGHT_ORG = colors.HexColor("#fbe9e7")
    LINE_ORG  = colors.HexColor("#ff8a65")

    company_style = ParagraphStyle("JCN", parent=styles["Normal"],
        fontSize=20, fontName="Helvetica-Bold", textColor=DARK_ORG, spaceAfter=6)
    tagline_style = ParagraphStyle("JTL", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica", textColor=MID_ORG, spaceBefore=0, spaceAfter=10)
    date_style    = ParagraphStyle("JDT", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", alignment=2)
    heading_style = ParagraphStyle("JHH", parent=styles["Normal"],
        fontSize=15, fontName="Helvetica-Bold", textColor=DARK_ORG,
        spaceBefore=10, spaceAfter=6, alignment=1)
    sub_style     = ParagraphStyle("JSH", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Bold", textColor=DARK_ORG,
        spaceBefore=12, spaceAfter=4)
    body_style    = ParagraphStyle("JBD", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", leading=16, spaceAfter=6)
    footer_style  = ParagraphStyle("JFT", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica", textColor=colors.grey, alignment=1)

    today_str    = date.today().strftime("%d %B %Y")
    name         = str(candidate_data.get("name")         or "Employee").strip()
    role         = str(candidate_data.get("role")         or "Associate").strip()
    email        = str(candidate_data.get("email")        or "").strip()
    phone        = str(candidate_data.get("phone")        or "").strip()
    loc          = str(candidate_data.get("location")     or "Chennai, Tamil Nadu").strip()
    dept         = str(candidate_data.get("department")   or "Technology").strip()
    emp_id       = str(candidate_data.get("employee_id")  or "—").strip()
    reporting_to = str(candidate_data.get("reporting_to") or "Department Manager").strip()
    ctc          = _rupees(candidate_data.get("offered_ctc") or
                           candidate_data.get("expected_salary") or 0)
    joining      = _fmt_date(candidate_data.get("joining_date"))

    story = []

    # Header
    story.append(Paragraph("Bit Byte Technologies.", company_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Empowering Talent  |  Building Tomorrow", tagline_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Date: {today_str}", date_style))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK_ORG, spaceAfter=10))

    # Title
    story.append(Paragraph("JOINING LETTER", heading_style))
    story.append(Spacer(1, 4))

    # Ref + address
    story.append(Paragraph(f"<b>Ref No:</b> BBT/JOIN/{date.today().year}/{emp_id}", body_style))
    story.append(Paragraph(f"<b>To,</b><br/><b>{name}</b>", body_style))
    story.append(Spacer(1, 6))

    # Opening
    story.append(Paragraph(
        f"This is to confirm that you have been inducted as <b>{role}</b> in the "
        f"<b>{dept}</b> department at <b>Bit Byte Technologies.</b>, "
        f"<b>{loc}</b>. Your joining date is recorded as <b>{joining}</b>.",
        body_style,
    ))

    # Joining details table
    story.append(Paragraph("Joining Details", sub_style))
    details = [
        ["Employee Name",   name],
        ["Employee ID",     emp_id],
        ["Designation",     role],
        ["Department",      dept],
        ["Reporting To",    reporting_to],
        ["Email",           email   or "—"],
        ["Phone",           phone   or "—"],
        ["Work Location",   loc],
        ["Date of Joining", joining],
    ]
    tbl = Table(details, colWidths=[5.5*cm, 10.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,-1), LIGHT_ORG),
        ("FONTNAME",   (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTNAME",   (1,0),(1,-1), "Helvetica"),
        ("FONTSIZE",   (0,0),(-1,-1), 10),
        ("GRID",       (0,0),(-1,-1), 0.5, LINE_ORG),
        ("PADDING",    (0,0),(-1,-1), 7),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [LIGHT_ORG, colors.white]),
    ]))
    story.append(tbl)

    # Compensation
    story.append(Paragraph("Compensation Summary", sub_style))
    comp_rows = [
        ["Component",        "Details"],
        ["Annual CTC",       ctc],
        ["Pay Cycle",        "Monthly (credited on last working day)"],
        ["Working Hours",    "9:00 AM - 6:00 PM (Monday to Friday)"],
        ["Work Location",    loc],
        ["Reporting To",     reporting_to],
    ]
    comp_tbl = Table(comp_rows, colWidths=[6*cm, 10*cm])
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,0), DARK_ORG),
        ("TEXTCOLOR",   (0,0),(-1,0), colors.white),
        ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTNAME",    (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,0),(-1,-1), 10),
        ("GRID",        (0,0),(-1,-1), 0.5, LINE_ORG),
        ("PADDING",     (0,0),(-1,-1), 7),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [LIGHT_ORG, colors.white]),
    ]))
    story.append(comp_tbl)

    # Documents checklist
    story.append(Paragraph("Documents to Submit on Joining Day", sub_style))
    docs = [
        "Original educational certificates (10th, 12th, Degree, PG if applicable)",
        "Previous employment relieving letter and experience certificates",
        "Last 3 months salary slips from previous employer",
        "Government ID proof (Aadhar Card / Passport / Voter ID)",
        "PAN Card (original and photocopy)",
        "2 passport-size photographs",
        "Bank account details (cancelled cheque or passbook copy)",
    ]
    for i, item in enumerate(docs, 1):
        story.append(Paragraph(f"{i}. {item}", body_style))

    # Instructions
    story.append(Paragraph("Joining Instructions", sub_style))
    instructions = [
        f"Please report to the HR department at <b>9:00 AM</b> on <b>{joining}</b>.",
        f"You will be reporting to <b>{reporting_to}</b> who will guide your onboarding process.",
        "Please carry all original documents mentioned above for verification.",
        "Dress code on joining day: Business Formals.",
        "For any queries, contact HR at hr@bitbyte.com or +91 44 0000 0000.",
    ]
    for i, inst in enumerate(instructions, 1):
        story.append(Paragraph(f"{i}. {inst}", body_style))

    # Closing
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "We are excited to have you on board and look forward to a great journey together. "
        "Please sign the duplicate copy of this letter and hand it over to HR on your joining day.",
        body_style,
    ))

    # Signature
    story.append(Spacer(1, 24))
    sig = Table([
        ["For Bit Byte Technologies.", "", "Accepted by"],
        ["",                           "", name],
        ["", "", ""],
        ["_______________________",    "", "_______________________"],
        ["HR Manager",                 "", f"Date: ____________________"],
    ], colWidths=[7*cm, 2*cm, 7*cm])
    sig.setStyle(TableStyle([
        ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0),(-1,-1), 9),
        ("FONTNAME", (0,1),(-1,-1), "Helvetica"),
        ("VALIGN",   (0,0),(-1,-1), "MIDDLE"),
        ("PADDING",  (0,0),(-1,-1), 3),
    ]))
    story.append(sig)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE_ORG))
    story.append(Paragraph(
        "Bit Byte Technologies.  |  Chennai, Tamil Nadu  |  hr@bitbyte.com  |  +91 44 0000 0000",
        footer_style,
    ))

    doc.build(story)
    return buffer.getvalue()


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_excel_generate_joining_pdf(request):
    """POST /api/generate-joining-letters/"""
    if "file" not in request.FILES:
        return Response({"error": "No file uploaded. Use key 'file'."}, status=400)
    try:
        _, candidates = _read_excel(request.FILES["file"])
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    required = {"name", "role"}
    missing  = required - set(candidates[0].keys())
    if missing:
        return Response({"error": f"Missing columns: {missing}"}, status=400)

    return _make_response(candidates, generate_joining_letter_pdf,
                          "joining_letter", "joining_letters.zip")


 # ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYMENT CONTRACT / AGREEMENT
# ══════════════════════════════════════════════════════════════════════════════

def generate_contract_letter_pdf(candidate_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm,     bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    DARK_PUR  = colors.HexColor("#4a148c")
    MID_PUR   = colors.HexColor("#7b1fa2")
    LIGHT_PUR = colors.HexColor("#f3e5f5")
    LINE_PUR  = colors.HexColor("#ce93d8")

    company_style = ParagraphStyle("CCN", parent=styles["Normal"],
        fontSize=20, fontName="Helvetica-Bold", textColor=DARK_PUR, spaceAfter=6)
    tagline_style = ParagraphStyle("CTL", parent=styles["Normal"],
        fontSize=9,  fontName="Helvetica", textColor=MID_PUR, spaceAfter=10)
    date_style    = ParagraphStyle("CDT", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", alignment=2)
    heading_style = ParagraphStyle("CHH", parent=styles["Normal"],
        fontSize=15, fontName="Helvetica-Bold", textColor=DARK_PUR,
        spaceBefore=10, spaceAfter=6, alignment=1)
    sub_style     = ParagraphStyle("CSH", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Bold", textColor=DARK_PUR,
        spaceBefore=12, spaceAfter=4)
    body_style    = ParagraphStyle("CBD", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", leading=16, spaceAfter=6)
    bold_body     = ParagraphStyle("CBB", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica-Bold", leading=16, spaceAfter=6)
    footer_style  = ParagraphStyle("CFT", parent=styles["Normal"],
        fontSize=8,  fontName="Helvetica", textColor=colors.grey, alignment=1)

    today_str    = date.today().strftime("%d %B %Y")
    name         = str(candidate_data.get("name")         or "Employee").strip()
    role         = str(candidate_data.get("role")         or "Associate").strip()
    email        = str(candidate_data.get("email")        or "").strip()
    phone        = str(candidate_data.get("phone")        or "").strip()
    loc          = str(candidate_data.get("location")     or "Chennai, Tamil Nadu").strip()
    dept         = str(candidate_data.get("department")   or "Technology").strip()
    emp_id       = str(candidate_data.get("employee_id")  or "—").strip()
    reporting_to = str(candidate_data.get("reporting_to") or "Department Manager").strip()
    bond_years   = str(candidate_data.get("bond_years")   or "2").strip()
    ctc          = _rupees(candidate_data.get("offered_ctc") or
                           candidate_data.get("expected_salary") or 0)
    joining      = _fmt_date(candidate_data.get("joining_date"))

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Bit Byte Technologies.", company_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Empowering Talent  |  Building Tomorrow", tagline_style))
    story.append(Paragraph(f"Date: {today_str}", date_style))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK_PUR, spaceAfter=10))

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("EMPLOYMENT CONTRACT AGREEMENT", heading_style))
    story.append(Paragraph(
        f"<b>Contract Ref No:</b> BBT/CONTRACT/{date.today().year}/{emp_id}",
        body_style))
    story.append(Spacer(1, 6))

    # ── Parties ───────────────────────────────────────────────────────────────
    story.append(Paragraph("This Employment Contract Agreement is entered into on "
        f"<b>{today_str}</b>, between:", body_style))

    parties = [
        ["EMPLOYER",  "Bit Byte Technologies., Chennai, Tamil Nadu\n(hereinafter referred to as 'the Company')"],
        ["EMPLOYEE",  f"{name}\nDesignation: {role} | Department: {dept}\n"
                      f"Employee ID: {emp_id}\n"
                      f"(hereinafter referred to as 'the Employee')"],
    ]
    p_tbl = Table(parties, colWidths=[3.5*cm, 12.5*cm])
    p_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), DARK_PUR),
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.white),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("GRID",        (0, 0), (-1, -1), 0.5, LINE_PUR),
        ("PADDING",     (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_PUR, colors.white]),
    ]))
    story.append(p_tbl)
    story.append(Spacer(1, 8))

    # ── Employment Details ────────────────────────────────────────────────────
    story.append(Paragraph("1. Employment Details", sub_style))
    details = [
        ["Full Name",        name],
        ["Employee ID",      emp_id],
        ["Designation",      role],
        ["Department",       dept],
        ["Reporting To",     reporting_to],
        ["Work Location",    loc],
        ["Email",            email or "—"],
        ["Phone",            phone or "—"],
        ["Date of Joining",  joining],
        ["Contract Date",    today_str],
    ]
    det_tbl = Table(details, colWidths=[5.5*cm, 10.5*cm])
    det_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (0, -1), LIGHT_PUR),
        ("FONTNAME",       (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",       (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("GRID",           (0, 0), (-1, -1), 0.5, LINE_PUR),
        ("PADDING",        (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_PUR, colors.white]),
    ]))
    story.append(det_tbl)

    # ── Compensation ──────────────────────────────────────────────────────────
    story.append(Paragraph("2. Compensation & Benefits", sub_style))
    story.append(Paragraph(
        f"The Employee shall be entitled to an annual Cost to Company (CTC) of <b>{ctc}</b>, "
        f"payable on a monthly basis. The salary structure will be communicated separately.",
        body_style))
    comp_rows = [
        ["Component",        "Details"],
        ["Annual CTC",       ctc],
        ["Pay Cycle",        "Monthly (last working day)"],
        ["Probation Period", "6 Months"],
        ["Working Hours",    "9:00 AM – 6:00 PM (Mon–Fri)"],
        ["Annual Leave",     "18 Days per year"],
        ["Sick Leave",       "6 Days per year"],
    ]
    comp_tbl = Table(comp_rows, colWidths=[6*cm, 10*cm])
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), DARK_PUR),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",       (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("GRID",           (0, 0), (-1, -1), 0.5, LINE_PUR),
        ("PADDING",        (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_PUR, colors.white]),
    ]))
    story.append(comp_tbl)

    # ── Bond Agreement ────────────────────────────────────────────────────────
    story.append(Paragraph(f"3. Service Bond Agreement ({bond_years}-Year Bond)", sub_style))
    story.append(Paragraph(
        f"The Employee agrees to serve <b>Bit Byte Technologies.</b> for a minimum period of "
        f"<b>{bond_years} ({_bond_words(bond_years)}) years</b> from the date of joining "
        f"(<b>{joining}</b>). This bond is entered into in consideration of the training, "
        f"resources, and opportunities provided by the Company.",
        body_style))

    bond_clauses = [
        f"The Employee shall not resign or leave the services of the Company before completing "
        f"{bond_years} year(s) from the date of joining without prior written consent.",
        f"In the event of early departure, the Employee shall be liable to pay a bond penalty of "
        f"<b>Rs. 1,00,000/- (Rupees One Lakh Only)</b> or the cost of training incurred by the "
        f"Company, whichever is higher.",
        "The bond amount shall be recovered from the employee's Full & Final Settlement or "
        "through legal proceedings if necessary.",
        "The bond obligation shall be waived only upon mutual written agreement by both parties.",
        "This bond clause is legally binding and enforceable under applicable Indian labour laws.",
    ]
    for i, clause in enumerate(bond_clauses, 1):
        story.append(Paragraph(f"  {i}. {clause}", body_style))

    # ── General Terms ─────────────────────────────────────────────────────────
    story.append(Paragraph("4. General Terms & Conditions", sub_style))
    general = [
        "The Employee shall devote full time and attention to the duties assigned.",
        "Confidential information of the Company shall not be disclosed during or after employment.",
        "The Employee shall not engage in any competing business or employment during tenure.",
        "Any intellectual property created during employment belongs solely to the Company.",
        "The Company reserves the right to transfer the Employee to any department or location.",
        "Misconduct, insubordination, or breach of policy may result in immediate termination.",
        "Upon termination or resignation, all Company property must be returned immediately.",
    ]
    for i, clause in enumerate(general, 1):
        story.append(Paragraph(f"  {i}. {clause}", body_style))

    # ── Termination ───────────────────────────────────────────────────────────
    story.append(Paragraph("5. Termination Clause", sub_style))
    story.append(Paragraph(
        "Either party may terminate this agreement by providing <b>60 days</b> written notice "
        "(30 days during probation). The Company may terminate immediately for gross misconduct "
        "without notice or payment in lieu thereof.", body_style))

    # ── Dispute Resolution ────────────────────────────────────────────────────
    story.append(Paragraph("6. Governing Law & Dispute Resolution", sub_style))
    story.append(Paragraph(
        "This Agreement shall be governed by the laws of India. Any disputes arising under "
        "this Agreement shall be subject to the exclusive jurisdiction of the courts in "
        "<b>Chennai, Tamil Nadu</b>.", body_style))

    # ── Declaration ───────────────────────────────────────────────────────────
    story.append(Paragraph("7. Declaration", sub_style))
    story.append(Paragraph(
        "Both parties hereby confirm that they have read, understood, and voluntarily agreed "
        "to all the terms and conditions set forth in this Employment Contract Agreement.",
        body_style))

    # ── Signature ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    sig = Table([
        ["For Bit Byte Technologies.",  "", f"Employee: {name}"],
        ["",                            "", f"Emp ID: {emp_id}"],
        ["", "", ""],
        ["_______________________",     "", "_______________________"],
        ["Authorised Signatory / HR",   "", f"Date: ____________________"],
        ["Date: ____________________",  "", ""],
    ], colWidths=[7*cm, 2*cm, 7*cm])
    sig.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 2), (-1, -1), "Helvetica"),
        ("VALIGN",   (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",  (0, 0), (-1, -1), 3),
    ]))
    story.append(sig)

    # ── Witness ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(Paragraph("Witnesses:", bold_body))
    witness = Table([
        ["Witness 1",               "", "Witness 2"],
        ["Name: _______________",   "", "Name: _______________"],
        ["Sign: _______________",   "", "Sign: _______________"],
        ["Date: _______________",   "", "Date: _______________"],
    ], colWidths=[7*cm, 2*cm, 7*cm])
    witness.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("PADDING",  (0, 0), (-1, -1), 3),
    ]))
    story.append(witness)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE_PUR))
    story.append(Paragraph(
        "Bit Byte Technologies.  |  Chennai, Tamil Nadu  |  hr@bitbyte.com  |  +91 44 0000 0000",
        footer_style))

    doc.build(story)
    return buffer.getvalue()


def _bond_words(years):
    words = {"1":"One","2":"Two","3":"Three","4":"Four","5":"Five"}
    return words.get(str(years), str(years))


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_excel_generate_contract_pdf(request):
    """POST /api/generate-contract-letters/"""
    if "file" not in request.FILES:
        return Response({"error": "No file uploaded. Use key 'file'."}, status=400)
    try:
        _, candidates = _read_excel(request.FILES["file"])
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    required = {"name", "role"}
    missing  = required - set(candidates[0].keys())
    if missing:
        return Response({"error": f"Missing columns: {missing}"}, status=400)

    return _make_response(candidates, generate_contract_letter_pdf,
                          "employment_contract", "employment_contracts.zip")                         