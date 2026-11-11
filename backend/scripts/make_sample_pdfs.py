"""Generate SYNTHETIC sample lab-report PDFs for tests and demos (spec §14.1).

All patients, labs, and values here are made up. Never use real patient data.

Run from the backend/ folder:
    python -m scripts.make_sample_pdfs

Writes the PDFs to backend/tests/fixtures/ and copies the demo-safe ones to
frontend/public/samples/ (for the "Try a sample report" button).
"""

import io
import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BACKEND_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = BACKEND_DIR / "tests" / "fixtures"
FRONTEND_SAMPLES_DIR = BACKEND_DIR.parent / "frontend" / "public" / "samples"

STYLES = getSampleStyleSheet()
HEADER = ["Test", "Result", "Unit", "Reference Range", "Flag"]

# A row is either a section heading (a 1-item tuple) or a full result row.
CBC_ROWS = [
    ("Red Blood Cells",),
    ("Haemoglobin", "10.8", "g/dL", "12.0 - 15.5", "L"),
    ("Hematocrit (PCV)", "33.1", "%", "36 - 46", "L"),
    ("RBC Count", "3.9", "million/µL", "4.2 - 5.4", "L"),
    ("MCV", "84.9", "fL", "80 - 100", ""),
    ("MCH", "27.7", "pg", "27 - 32", ""),
    ("MCHC", "32.6", "g/dL", "32 - 36", ""),
    ("RDW", "13.8", "%", "11.5 - 14.5", ""),
    ("White Blood Cells",),
    ("Total WBC Count", "7,200", "/µL", "4,000 - 11,000", ""),
    ("Neutrophils", "62", "%", "40 - 75", ""),
    ("Lymphocytes", "30", "%", "20 - 45", ""),
    ("Monocytes", "5", "%", "2 - 10", ""),
    ("Eosinophils", "3", "%", "1 - 6", ""),
    ("Platelets",),
    ("Platelet Count", "2,45,000", "/µL", "1,50,000 - 4,10,000", ""),
]

LIPID_ROWS = [
    ("Lipid Profile",),
    ("Total Cholesterol", "228", "mg/dL", "Desirable < 200", "H"),
    ("LDL Cholesterol", "162", "mg/dL", "< 100", "H"),
    ("HDL Cholesterol", "38", "mg/dL", "> 40", "L"),
    ("Triglycerides", "180", "mg/dL", "< 150", "H"),
    ("VLDL Cholesterol", "36", "mg/dL", "< 30", "H"),
    ("Non-HDL Cholesterol", "190", "mg/dL", "< 130", "H"),
]

THYROID_METABOLIC_ROWS = [
    ("Thyroid Function",),
    ("TSH", "3.2", "µIU/mL", "0.4 - 4.0", ""),
    ("Free T4", "1.1", "ng/dL", "0.8 - 1.8", ""),
    ("Blood Sugar",),
    ("Fasting Blood Glucose", "104", "mg/dL", "70 - 99", "H"),
    ("HbA1c", "6.1", "%", "Normal < 5.7, Prediabetes 5.7-6.4", "H"),
    ("Kidney Function",),
    ("Creatinine", "0.9", "mg/dL", "0.6 - 1.2", ""),
    ("eGFR", "88", "mL/min/1.73m²", "> 60", ""),
    ("Electrolytes",),
    ("Sodium", "139", "mmol/L", "136 - 145", ""),
    ("Potassium", "6.4", "mmol/L", "3.5 - 5.1", "HH CRITICAL"),
    ("Urine Examination",),
    ("Urine Glucose", "Negative", "", "Negative", ""),
]


def _patient_block(patient: str, age: str, sex: str, date: str, lab: str) -> list:
    """Header lines that look like a typical lab report (all fictional)."""
    s = STYLES["Normal"]
    return [
        Paragraph(f"<b>{lab}</b>", STYLES["Title"]),
        Paragraph("12 Example Road, Sample City — SYNTHETIC TEST DOCUMENT", s),
        Spacer(1, 4 * mm),
        Paragraph(f"Patient: {patient} &nbsp;&nbsp; Age: {age} &nbsp;&nbsp; Sex: {sex}", s),
        Paragraph(f"Report Date: {date} &nbsp;&nbsp; Sample ID: SYN-0000", s),
        Spacer(1, 5 * mm),
    ]


def _results_table(rows: list[tuple]) -> Table:
    data = [HEADER]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0bec5")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]
    for row in rows:
        if len(row) == 1:  # section heading spans the whole row
            data.append([row[0], "", "", "", ""])
            r = len(data) - 1
            style += [
                ("SPAN", (0, r), (-1, r)),
                ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
                ("BACKGROUND", (0, r), (-1, r), colors.HexColor("#e3f2fd")),
            ]
        else:
            data.append(list(row))
            if row[4]:  # bold the flag so it stands out, like real reports
                style.append(("FONTNAME", (4, len(data) - 1), (4, len(data) - 1), "Helvetica-Bold"))
    table = Table(data, colWidths=[55 * mm, 22 * mm, 28 * mm, 55 * mm, 25 * mm])
    table.setStyle(TableStyle(style))
    return table


def _footer() -> list:
    s = STYLES["Italic"]
    return [
        Spacer(1, 6 * mm),
        Paragraph("Reference ranges are specific to this laboratory.", s),
        Paragraph("This is a synthetic report generated for software testing only.", s),
        Paragraph("*** End of Report ***", s),
    ]


def build_report_pdf(path: Path, title: str, patient_args: tuple, rows: list[tuple]) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=A4, title=title)
    story = _patient_block(*patient_args)
    story.append(Paragraph(f"<b>{title}</b>", STYLES["Heading2"]))
    story.append(_results_table(rows))
    story += _footer()
    doc.build(story)


def build_scanned_like_pdf(path: Path) -> None:
    """A PDF with NO text layer: the 'report' is drawn as a raster image.

    This mimics a scanned/photographed report and must trigger SCANNED_PDF_UNSUPPORTED.
    We render text into a PNG with PyMuPDF and then place only that image on the page.
    """
    import pymupdf as fitz

    # 1) Make a PDF page with text, rasterize it to a PNG image.
    tmp = fitz.open()
    page = tmp.new_page(width=595, height=842)
    page.insert_text((60, 100), "Sample Diagnostics Lab", fontsize=20)
    page.insert_text((60, 140), "Haemoglobin   10.8 g/dL   12.0 - 15.5   L", fontsize=12)
    page.insert_text((60, 160), "Platelets     2,45,000 /uL", fontsize=12)
    png_bytes = page.get_pixmap(dpi=100).tobytes("png")
    tmp.close()

    # 2) Put only the image into a new PDF (no text layer at all).
    c = canvas.Canvas(str(path), pagesize=A4)
    from reportlab.lib.utils import ImageReader

    c.drawImage(ImageReader(io.BytesIO(png_bytes)), 0, 0, width=A4[0], height=A4[1])
    c.showPage()
    c.save()


def build_not_a_report_pdf(path: Path) -> None:
    """Plain prose with no lab results — must trigger NOT_A_LAB_REPORT."""
    lorem = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure "
        "dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
    )
    doc = SimpleDocTemplate(str(path), pagesize=A4, title="Not a report")
    story = [Paragraph("A Short Essay", STYLES["Title"])]
    story += [Paragraph(lorem, STYLES["Normal"]) for _ in range(4)]
    doc.build(story)


def build_encrypted_pdf(path: Path, source: Path) -> None:
    """Password-protected copy of a report — must trigger ENCRYPTED_PDF."""
    import pymupdf as fitz

    doc = fitz.open(source)
    doc.save(
        str(path),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="secret",
        owner_pw="owner-secret",
    )
    doc.close()


def build_too_many_pages_pdf(path: Path, pages: int = 21) -> None:
    """A text PDF with more pages than MAX_PDF_PAGES — must trigger TOO_MANY_PAGES."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(pages):
        c.drawString(72, 750, f"Page {i + 1} of a long synthetic document.")
        c.showPage()
    c.save()


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    cbc = FIXTURES_DIR / "sample_cbc_low_hb.pdf"
    lipid = FIXTURES_DIR / "sample_lipid_high_ldl.pdf"
    thyroid = FIXTURES_DIR / "sample_thyroid_metabolic_mixed.pdf"

    build_report_pdf(
        cbc,
        "Complete Blood Count (CBC)",
        ("Sample Patient A", "34", "Female", "2026-10-02", "Sample Diagnostics Lab"),
        CBC_ROWS,
    )
    build_report_pdf(
        lipid,
        "Lipid Profile",
        ("Sample Patient B", "45", "Male", "2026-10-05", "Example Health Laboratory"),
        LIPID_ROWS,
    )
    build_report_pdf(
        thyroid,
        "Thyroid & Metabolic Panel",
        ("Sample Patient C", "72", "Female", "2026-10-08", "Demo Pathology Centre"),
        THYROID_METABOLIC_ROWS,
    )
    build_scanned_like_pdf(FIXTURES_DIR / "scanned_like.pdf")
    build_not_a_report_pdf(FIXTURES_DIR / "not_a_report.pdf")
    build_encrypted_pdf(FIXTURES_DIR / "encrypted.pdf", cbc)
    build_too_many_pages_pdf(FIXTURES_DIR / "too_many_pages.pdf")

    # Copy the files used by the frontend demo ("Try a sample report", error demo).
    for name in [
        "sample_cbc_low_hb.pdf",
        "sample_lipid_high_ldl.pdf",
        "sample_thyroid_metabolic_mixed.pdf",
        "scanned_like.pdf",
    ]:
        shutil.copy(FIXTURES_DIR / name, FRONTEND_SAMPLES_DIR / name)

    print(f"Wrote sample PDFs to {FIXTURES_DIR}")
    print(f"Copied demo samples to {FRONTEND_SAMPLES_DIR}")


if __name__ == "__main__":
    main()
