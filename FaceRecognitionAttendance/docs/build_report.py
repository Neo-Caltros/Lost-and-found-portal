"""Build the project report and its original diagram images.

Run with the bundled workspace Python or any Python environment containing
python-docx and Pillow. The generated DOCX is checked separately with the
document renderer before it is delivered.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "diagram_assets"
OUTPUT = DOCS / "Face_Recognition_Attendance_System_Project_Report.docx"
NAVY = RGBColor(11, 37, 69)
BLUE = RGBColor(46, 116, 181)
MUTED = RGBColor(85, 93, 107)
LIGHT_FILL = "F2F4F7"
ACCENT_FILL = "E8EEF5"


def font(size: int, bold: bool = False):
    """Use a Windows font when possible and a portable fallback otherwise."""
    candidates = (
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
    )
    if bold:
        candidates = ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", *candidates)
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = "#2E74B5") -> None:
    draw.line((start, end), fill=color, width=5)
    x_end, y_end = end
    x_start, y_start = start
    if abs(x_end - x_start) >= abs(y_end - y_start):
        direction = 1 if x_end > x_start else -1
        points = [(x_end, y_end), (x_end - direction * 20, y_end - 11), (x_end - direction * 20, y_end + 11)]
    else:
        direction = 1 if y_end > y_start else -1
        points = [(x_end, y_end), (x_end - 11, y_end - direction * 20), (x_end + 11, y_end - direction * 20)]
    draw.polygon(points, fill=color)


def rounded_box(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    text: str,
    fill: str = "#E8EEF5",
    outline: str = "#2E74B5",
    text_fill: str = "#0B2545",
) -> None:
    draw.rounded_rectangle(bounds, radius=18, fill=fill, outline=outline, width=4)
    text_box = draw.multiline_textbbox((0, 0), text, font=font(26, True), align="center", spacing=5)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    center_x = (bounds[0] + bounds[2] - text_width) / 2
    center_y = (bounds[1] + bounds[3] - text_height) / 2
    draw.multiline_text((center_x, center_y), text, font=font(26, True), fill=text_fill, align="center", spacing=5)


def diagram_header(draw: ImageDraw.ImageDraw, title: str) -> None:
    draw.rectangle((0, 0, 1500, 850), fill="white")
    draw.text((60, 35), title, font=font(40, True), fill="#0B2545")
    draw.line((60, 98, 1440, 98), fill="#D7DBE2", width=3)


def make_er_diagram() -> Path:
    path = ASSETS / "er_diagram.png"
    image = Image.new("RGB", (1500, 850), "white")
    draw = ImageDraw.Draw(image)
    diagram_header(draw, "Entity Relationship Diagram")
    left = (130, 170, 650, 650)
    right = (850, 170, 1370, 650)
    for box, title, rows in (
        (left, "STUDENTS", ["PK  id : INTEGER", "UK  student_id : TEXT", "name : TEXT", "department : TEXT", "semester : TEXT"]),
        (right, "ATTENDANCE", ["PK  id : INTEGER", "student_id : TEXT", "name : TEXT", "date : TEXT", "time : TEXT", "status : TEXT"]),
    ):
        draw.rounded_rectangle(box, radius=18, fill="#F7F9FC", outline="#2E74B5", width=4)
        draw.rounded_rectangle((box[0], box[1], box[2], box[1] + 78), radius=18, fill="#2E74B5")
        draw.rectangle((box[0], box[1] + 42, box[2], box[1] + 78), fill="#2E74B5")
        draw.text((box[0] + 24, box[1] + 20), title, font=font(28, True), fill="white")
        y_pos = box[1] + 115
        for row in rows:
            draw.text((box[0] + 30, y_pos), row, font=font(23), fill="#1F2937")
            draw.line((box[0] + 22, y_pos + 43, box[2] - 22, y_pos + 43), fill="#D7DBE2", width=2)
            y_pos += 66
    arrow(draw, (650, 410), (850, 410))
    draw.text((674, 360), "1 marks", font=font(22), fill="#4B5563")
    draw.text((690, 435), "many", font=font(22), fill="#4B5563")
    image.save(path)
    return path


def make_architecture_diagram() -> Path:
    path = ASSETS / "architecture_diagram.png"
    image = Image.new("RGB", (1500, 850), "white")
    draw = ImageDraw.Draw(image)
    diagram_header(draw, "System Architecture")
    nodes = [
        (80, 180, 300, 310, "Administrator"),
        (390, 180, 660, 310, "Tkinter\nDashboard"),
        (760, 180, 1040, 310, "Application\nModules"),
        (1140, 180, 1420, 310, "SQLite / CSV\nStorage"),
        (390, 500, 660, 630, "Webcam + Haar\nFace Detection"),
        (850, 500, 1120, 630, "Dataset + LBPH\nModel"),
    ]
    for node in nodes:
        rounded_box(draw, node[:4], node[4])
    arrow(draw, (300, 245), (390, 245))
    arrow(draw, (660, 245), (760, 245))
    arrow(draw, (1040, 245), (1140, 245))
    arrow(draw, (525, 310), (525, 500))
    arrow(draw, (900, 310), (980, 500))
    arrow(draw, (660, 565), (850, 565))
    image.save(path)
    return path


def make_flowchart() -> Path:
    path = ASSETS / "flowchart.png"
    image = Image.new("RGB", (1500, 1050), "white")
    draw = ImageDraw.Draw(image)
    diagram_header(draw, "Attendance Workflow")
    steps = [
        (570, 140, 930, 225, "Admin Login"),
        (570, 295, 930, 380, "Dashboard Action"),
        (570, 450, 930, 535, "Open Webcam"),
        (570, 605, 930, 690, "Detect Face (Haar)"),
        (570, 760, 930, 845, "Recognize Face (LBPH)"),
        (570, 915, 930, 1000, "Mark Present Once Per Day"),
    ]
    for step in steps:
        rounded_box(draw, step[:4], step[4])
    for upper, lower in zip(steps, steps[1:]):
        arrow(draw, ((upper[0] + upper[2]) // 2, upper[3]), ((lower[0] + lower[2]) // 2, lower[1]))
    image.save(path)
    return path


def make_use_case_diagram() -> Path:
    path = ASSETS / "use_case_diagram.png"
    image = Image.new("RGB", (1500, 850), "white")
    draw = ImageDraw.Draw(image)
    diagram_header(draw, "Use Case Diagram")
    # Actor
    draw.ellipse((125, 230, 205, 310), outline="#0B2545", width=4)
    draw.line((165, 310, 165, 435), fill="#0B2545", width=5)
    draw.line((110, 355, 220, 355), fill="#0B2545", width=5)
    draw.line((165, 435, 115, 510), fill="#0B2545", width=5)
    draw.line((165, 435, 215, 510), fill="#0B2545", width=5)
    draw.text((95, 540), "Administrator", font=font(25, True), fill="#0B2545")
    cases = [
        (460, 150, 800, 245, "Log in"),
        (920, 150, 1260, 245, "Register student"),
        (460, 330, 800, 425, "Train / retrain model"),
        (920, 330, 1260, 425, "Take attendance"),
        (460, 510, 800, 605, "View / search records"),
        (920, 510, 1260, 605, "Export CSV"),
    ]
    for use_case in cases:
        draw.ellipse(use_case[:4], fill="#E8EEF5", outline="#2E74B5", width=4)
        text_box = draw.multiline_textbbox((0, 0), use_case[4], font=font(24, True), align="center")
        tx = (use_case[0] + use_case[2] - (text_box[2] - text_box[0])) / 2
        ty = (use_case[1] + use_case[3] - (text_box[3] - text_box[1])) / 2
        draw.multiline_text((tx, ty), use_case[4], font=font(24, True), fill="#0B2545", align="center")
        draw.line((220, 355, use_case[0], (use_case[1] + use_case[3]) // 2), fill="#7B8798", width=3)
    image.save(path)
    return path


def make_sequence_diagram() -> Path:
    path = ASSETS / "sequence_diagram.png"
    image = Image.new("RGB", (1500, 950), "white")
    draw = ImageDraw.Draw(image)
    diagram_header(draw, "Sequence Diagram - Take Attendance")
    actors = [(190, "Admin"), (510, "Tkinter GUI"), (850, "OpenCV / Model"), (1190, "SQLite")]
    for x_pos, label in actors:
        rounded_box(draw, (x_pos - 110, 135, x_pos + 110, 205), label, fill="#E8EEF5")
        draw.line((x_pos, 205, x_pos, 890), fill="#8A99AC", width=3)
    arrows = [
        (260, 510, 280, "Click Take Attendance"),
        (580, 850, 400, "Load model / start camera"),
        (920, 510, 520, "Face + prediction label"),
        (580, 1190, 640, "Look up student / insert Present"),
        (1120, 510, 760, "Attendance result"),
        (440, 850, 840, "Q or Esc stops loop"),
    ]
    for start_x, end_x, y_pos, label in arrows:
        arrow(draw, (start_x, y_pos), (end_x, y_pos))
        draw.text(((start_x + end_x) // 2 - 110, y_pos - 36), label, font=font(20), fill="#374151")
    image.save(path)
    return path


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    tc_pr.append(shading)


def set_cell_margins(cell, top: int = 80, start: int = 120, bottom: int = 80, end: int = 120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for margin_name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{margin_name}"))
        if node is None:
            node = OxmlElement(f"w:{margin_name}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_widths(table, widths: list[int]) -> None:
    table.autofit = False
    table_pr = table._tbl.tblPr
    table_width = table_pr.first_child_found_in("w:tblW")
    table_width.set(qn("w:w"), str(sum(widths)))
    table_width.set(qn("w:type"), "dxa")
    table_indent = OxmlElement("w:tblInd")
    table_indent.set(qn("w:w"), "120")
    table_indent.set(qn("w:type"), "dxa")
    table_pr.append(table_indent)
    grid = table._tbl.tblGrid
    for column, width in zip(grid.gridCol_lst, widths):
        column.set(qn("w:w"), str(width))
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = Inches(width / 1440)
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_width = tc_pr.first_child_found_in("w:tcW")
            tc_width.set(qn("w:w"), str(width))
            tc_width.set(qn("w:type"), "dxa")
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)


def set_run_font(run, size: float | None = None, color: RGBColor | None = None, bold: bool | None = None) -> None:
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color
    if bold is not None:
        run.bold = bold


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)
    section.different_first_page_header_footer = True

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.10
    for name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 16, 8),
        ("Heading 2", 13, BLUE, 12, 6),
        ("Heading 3", 12, NAVY, 8, 4),
    ):
        style = styles[name]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        style.font.size = Pt(size)
        style.font.color.rgb = color
        style.font.bold = True
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_run = header.add_run("Face Recognition Attendance System | Project Report")
    set_run_font(header_run, 8.5, MUTED)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("CSE Mini Project | Page ")
    set_run_font(footer_run, 8.5, MUTED)
    add_page_field(footer)


def add_page_field(paragraph) -> None:
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    paragraph._p.append(field)


def add_title(document: Document, text: str, subtitle: str | None = None) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(138)
    paragraph.paragraph_format.space_after = Pt(12)
    run = paragraph.add_run(text)
    set_run_font(run, 30, NAVY, True)
    if subtitle:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(36)
        run = paragraph.add_run(subtitle)
        set_run_font(run, 15, MUTED)


def add_paragraph(document: Document, text: str, *, bold_lead: str | None = None) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.10
    if bold_lead and text.startswith(bold_lead):
        lead = paragraph.add_run(bold_lead)
        set_run_font(lead, bold=True)
        rest = paragraph.add_run(text[len(bold_lead) :])
        set_run_font(rest)
    else:
        run = paragraph.add_run(text)
        set_run_font(run)


def add_bullets(document: Document, bullets: list[str]) -> None:
    for item in bullets:
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.paragraph_format.line_spacing = 1.15
        run = paragraph.add_run(item)
        set_run_font(run)


def add_numbered(document: Document, entries: list[str]) -> None:
    for entry in entries:
        paragraph = document.add_paragraph(style="List Number")
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.paragraph_format.line_spacing = 1.15
        run = paragraph.add_run(entry)
        set_run_font(run)


def add_table(document: Document, headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    set_table_widths(table, widths)
    for cell, header in zip(table.rows[0].cells, headers):
        set_cell_shading(cell, LIGHT_FILL)
        paragraph = cell.paragraphs[0]
        run = paragraph.add_run(header)
        set_run_font(run, 10, NAVY, True)
    for row_values in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row_values):
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run(value)
            set_run_font(run, 9.5)
    for row in table.rows:
        for cell in row.cells:
            set_cell_margins(cell)


def page_break(document: Document) -> None:
    document.add_page_break()


def build_report() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    er = make_er_diagram()
    architecture = make_architecture_diagram()
    flowchart = make_flowchart()
    use_case = make_use_case_diagram()
    sequence = make_sequence_diagram()

    document = Document()
    configure_document(document)

    # 1. Cover
    add_title(document, "FACE RECOGNITION\nATTENDANCE SYSTEM", "Second-Year Computer Science Engineering Project")
    for label, value in (
        ("Technology Stack", "Python, Tkinter, SQLite, OpenCV Haar Cascade and LBPH"),
        ("Platform", "Windows with Python 3.11+"),
        ("Project Type", "Desktop-based Automated Attendance System"),
    ):
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(10)
        label_run = paragraph.add_run(f"{label}: ")
        set_run_font(label_run, 11, NAVY, True)
        value_run = paragraph.add_run(value)
        set_run_font(value_run, 11, MUTED)
    document.add_paragraph().add_run("\n\nSubmitted as a mini project for the Second-Year Computer Science Engineering curriculum.")
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    page_break(document)

    # 2. Certificate and declaration
    document.add_heading("Certificate and Declaration", level=1)
    add_paragraph(document, "This report presents the design and implementation of the Face Recognition Attendance System, a desktop application developed as an educational Computer Science Engineering project. The work demonstrates local database design, graphical user interface development, computer vision, and software testing using Python.")
    add_paragraph(document, "The system is intended for controlled academic demonstrations. It captures student face samples with consent, trains a local LBPH recognizer, and records attendance without requiring a cloud service.")
    document.add_heading("Academic Integrity Statement", level=2)
    add_paragraph(document, "The implementation is modular and the documentation explains the purpose of each component, the design choices, known limitations, and the tests that should be performed before a classroom demonstration.")
    document.add_paragraph("\n\n")
    signature = document.add_paragraph()
    signature.paragraph_format.space_before = Pt(80)
    signature.add_run("Student Signature: ____________________\n\nFaculty Guide Signature: ____________________")
    page_break(document)

    # 3. Acknowledgement and abstract
    document.add_heading("Acknowledgement", level=1)
    add_paragraph(document, "The project acknowledges the guidance normally provided by department faculty, the support of classmates who assist with testing, and the open-source Python and OpenCV communities whose tools make hands-on computer vision education accessible.")
    document.add_heading("Abstract", level=1)
    add_paragraph(document, "Manual attendance is slow, repetitive, and vulnerable to proxy marking or transcription mistakes. This project implements a local Face Recognition Attendance System that registers a student, captures face images through a webcam, trains an OpenCV LBPH model, recognizes faces in real time, and automatically records Present status in an SQLite database.")
    add_paragraph(document, "The application uses a Tkinter interface so it can run easily on Windows in Visual Studio Code. A Haar Cascade detects a face in every camera frame before the recognizer predicts the student label. The database guarantees that a student receives no more than one attendance entry on the same date. Operators can search records and export them to CSV. The final solution is suitable as a clearly scoped academic project and an extensible base for more advanced biometric attendance research.")
    document.add_heading("Keywords", level=2)
    add_bullets(document, ["Face recognition", "Automated attendance", "OpenCV", "LBPH", "Haar Cascade", "SQLite", "Tkinter"])
    page_break(document)

    # 4. Contents
    document.add_heading("Table of Contents", level=1)
    contents = [
        "1. Introduction and Objectives", "2. Technology Background", "3. Requirements and Module Design", "4. Data Design and ER Diagram", "5. Architecture, Use Cases, and Workflow", "6. Implementation Details", "7. Testing and Results", "8. Limitations and Future Scope", "9. Conclusion and References",
    ]
    add_numbered(document, contents)
    document.add_heading("List of Figures", level=2)
    add_bullets(document, ["Figure 1: Entity Relationship Diagram", "Figure 2: System Architecture", "Figure 3: Attendance Workflow", "Figure 4: Use Case Diagram", "Figure 5: Attendance Sequence Diagram"])
    document.add_heading("List of Tables", level=2)
    add_bullets(document, ["Table 1: Functional Requirements", "Table 2: Module Responsibilities", "Table 3: Database Data Dictionary", "Table 4: Test Summary"])
    page_break(document)

    # 5. Introduction
    document.add_heading("1. Introduction and Objectives", level=1)
    add_paragraph(document, "Attendance is an essential administrative activity in schools and colleges. Paper registers require time at the start of every class and are difficult to consolidate for reporting. RFID cards and manual spreadsheets reduce some work but do not confirm that the registered person is physically present. Face recognition offers a contactless way to associate a visible person with a stored student record.")
    document.add_heading("Problem Statement", level=2)
    add_paragraph(document, "The problem is to build a low-cost, local desktop system that captures student face samples, identifies a known student through a webcam, and records attendance without duplicate entries on the same day.")
    document.add_heading("Objectives", level=2)
    add_bullets(document, ["Provide administrator-only access to attendance functions.", "Register student metadata and collect 50-100 local face samples.", "Train an OpenCV LBPH recognizer from the local dataset.", "Detect and recognize faces in real time with a visible confidence indicator.", "Store Present attendance once per day and make records searchable/exportable.", "Offer maintainable modules, clear errors, and repeatable tests."])
    document.add_heading("Scope", level=2)
    add_paragraph(document, "The project is designed for one local Windows computer with one connected webcam. It deliberately uses SQLite and local folders instead of a network server, making setup simple for a laboratory demonstration. It is not presented as a high-security biometric access-control system.")
    page_break(document)

    # 6. Technology
    document.add_heading("2. Technology Background", level=1)
    add_table(document, ["Technology", "Role in the System", "Reason for Selection"], [
        ["Python 3.11+", "Application language", "Readable syntax and strong ecosystem for GUI, databases, and vision."],
        ["Tkinter", "Desktop GUI", "Bundled with Python and appropriate for a lightweight Windows desktop interface."],
        ["SQLite", "Local database", "Serverless, reliable, and easy to back up as a single file."],
        ["OpenCV Haar Cascade", "Face detection", "Fast classical detector used to locate a face before recognition."],
        ["OpenCV LBPH", "Face recognition", "Practical educational recognizer that works with grayscale local images."],
        ["CSV", "Interchange/export", "Readable by Excel and other spreadsheet applications."],
    ], [1800, 3550, 4010])
    document.add_heading("Haar Cascade Detection", level=2)
    add_paragraph(document, "The Haar Cascade classifier scans grayscale frames for facial patterns. Its output is a rectangle around the detected face. The application crops and resizes that region to 200 x 200 pixels before sending it to the recognizer. This reduces background variation and keeps training data consistent.")
    document.add_heading("LBPH Recognition", level=2)
    add_paragraph(document, "Local Binary Patterns Histograms encode local intensity differences around pixels. The LBPH recognizer compares a captured face crop against the trained histograms and returns a label plus a distance. A lower distance indicates a closer match. The application displays a derived percentage for usability but uses a conservative distance threshold to decide whether the face is known.")
    page_break(document)

    # 7. Requirements and modules
    document.add_heading("3. Requirements and Module Design", level=1)
    document.add_heading("Functional Requirements", level=2)
    add_table(document, ["ID", "Requirement", "Implementation"], [
        ["FR-01", "Administrator login", "Local password dialog using environment-configurable credentials."],
        ["FR-02", "Student registration", "Validated ID, name, department, semester, and webcam capture."],
        ["FR-03", "Model training", "LBPH model saved as trainer/trainer.yml."],
        ["FR-04", "Automatic attendance", "Recognition inserts Present through a unique SQLite constraint."],
        ["FR-05", "Record management", "Search, CSV export, deletion, statistics, and backup."],
    ], [900, 2600, 5860])
    document.add_heading("Module Responsibilities", level=2)
    add_table(document, ["Module", "Responsibility"], [
        ["main.py", "Builds the dark-mode dashboard and coordinates all user actions."],
        ["login.py", "Validates administrator credentials before access is granted."],
        ["register.py", "Stores student details, captures face crops, lists and deletes students."],
        ["train.py", "Reads dataset images, trains LBPH, writes the model and metadata."],
        ["recognize.py", "Runs webcam detection/prediction and marks attendance."],
        ["attendance.py", "Displays, searches, and exports attendance records."],
        ["database.py", "Encapsulates SQLite schema, queries, export, and statistics."],
        ["utils.py", "Provides project paths, validation, camera, cascade, and LBPH helpers."],
    ], [2100, 7260])
    page_break(document)

    # 8 Data Design
    document.add_heading("4. Data Design and ER Diagram", level=1)
    add_paragraph(document, "The SQLite database contains two tables. Students preserves the identity details used during registration. Attendance is intentionally denormalized with the student name so exported records remain easy to read, while student_id is constrained with date to prevent duplicate daily attendance.")
    document.add_picture(str(er), width=Inches(6.35))
    caption = document.add_paragraph("Figure 1. Entity Relationship Diagram")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.runs[0].italic = True
    document.add_heading("Data Dictionary", level=2)
    add_table(document, ["Table", "Key Fields", "Purpose"], [
        ["Students", "id (PK), student_id (UNIQUE)", "Stores registered student identity and academic fields."],
        ["Attendance", "id (PK), UNIQUE(student_id, date)", "Stores each student's daily Present record and timestamp."],
    ], [1500, 3600, 4260])
    page_break(document)

    # 9 architecture and use cases
    document.add_heading("5. Architecture, Use Cases, and Workflow", level=1)
    document.add_picture(str(architecture), width=Inches(5.70))
    caption = document.add_paragraph("Figure 2. System Architecture")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.runs[0].italic = True
    add_paragraph(document, "The GUI directs each action to a dedicated module. Registration and recognition interact with the webcam. Training consumes saved face crops and produces a local model. The database module is the single point for persistence and export, which keeps SQL logic separate from interface code.")
    document.add_picture(str(use_case), width=Inches(5.70))
    caption = document.add_paragraph("Figure 3. Use Case Diagram")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.runs[0].italic = True
    page_break(document)

    # 10 Flow and Sequence
    document.add_heading("5.1 Attendance Workflow and Sequence", level=1)
    document.add_picture(str(flowchart), width=Inches(4.45))
    caption = document.add_paragraph("Figure 4. Attendance Workflow")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.runs[0].italic = True
    add_paragraph(document, "The workflow begins after successful administrator login. A face must first be detected, then matched below the LBPH distance threshold. For a valid student, the system attempts an insert. The database's UNIQUE(student_id, date) constraint safely rejects any repeated daily entry.")
    document.add_picture(str(sequence), width=Inches(5.30))
    caption = document.add_paragraph("Figure 5. Attendance Sequence Diagram")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.runs[0].italic = True
    page_break(document)

    # 11 Implementation
    document.add_heading("6. Implementation Details", level=1)
    document.add_heading("Registration and Dataset Capture", level=2)
    add_paragraph(document, "Before opening the camera, the application validates all text fields and inserts the student using a unique Student ID. Captured images are grayscale face crops stored as user.<database-id>.<image-number>.jpg. If capture produces no usable image, the newly inserted student is removed to avoid an incomplete record.")
    document.add_heading("Model Training and Recognition", level=2)
    add_paragraph(document, "Training reads valid dataset filenames, resizes each crop to a consistent size, and trains the LBPH recognizer. The model is saved to trainer.yml along with lightweight JSON metadata. During recognition, the saved label is an internal student database ID, which allows the program to support Student IDs containing letters as well as numbers.")
    document.add_heading("Duplicate Prevention and Error Handling", level=2)
    add_bullets(document, ["Students.student_id has a UNIQUE constraint to reject duplicate registration.", "Attendance has UNIQUE(student_id, date), preventing duplicate daily Present entries even when the camera sees repeated frames.", "Camera open/read failures, missing model files, corrupt images, and missing OpenCV-contrib support result in actionable messages.", "Deleting a student removes their face images and attendance history; the dashboard reminds the operator to retrain the model.", "A timestamped SQLite backup can be generated from the dashboard."])
    document.add_heading("Security and Privacy", level=2)
    add_paragraph(document, "The default password is suitable only for an academic demonstration. The login credentials can be changed through environment variables. Face images are biometric data; students should be informed, consent should be obtained, access to the device should be restricted, and dataset retention should follow institutional policy.")
    page_break(document)

    # 12 Testing
    document.add_heading("7. Testing and Results", level=1)
    add_paragraph(document, "The project includes a unittest suite that exercises data storage, duplicate handling, CSV export, synthetic-image LBPH training, confidence threshold logic, and invalid-webcam handling. Camera-dependent behavior is additionally tested manually on the intended Windows device.")
    add_table(document, ["Test", "Expected Outcome", "Result"], [
        ["Student registration", "Valid student is stored; duplicate ID is rejected.", "Pass - automated"],
        ["Model training", "Synthetic face crops create a readable trainer.yml.", "Pass - automated"],
        ["Attendance recording", "Second insert for the same student/date is blocked.", "Pass - automated"],
        ["CSV export", "Header and matching records are written in UTF-8 CSV.", "Pass - automated"],
        ["Invalid webcam", "CameraError is raised without a crash.", "Pass - automated"],
        ["Unknown face", "Threshold helper returns unknown; no record is created.", "Pass - automated/manual"],
        ["Live recognition", "Known face is displayed and marked once per day.", "Manual on target webcam"],
    ], [2000, 5000, 2360])
    document.add_heading("Test Command", level=2)
    code = document.add_paragraph()
    code.paragraph_format.left_indent = Inches(0.25)
    code.paragraph_format.space_before = Pt(8)
    code.paragraph_format.space_after = Pt(10)
    run = code.add_run("python -m unittest discover -s tests -v")
    set_run_font(run, 10, NAVY)
    document.add_heading("Acceptance Criteria", level=2)
    add_bullets(document, ["A valid registration stores student data and face images.", "Training creates trainer/trainer.yml from local samples.", "A recognized student receives only one Present record per date.", "The attendance viewer returns filtered records and CSV output.", "A missing model or unavailable webcam is handled gracefully."])
    page_break(document)

    # 13 limits/future scope
    document.add_heading("8. Limitations and Future Scope", level=1)
    document.add_heading("Current Limitations", level=2)
    add_bullets(document, ["Haar Cascade and LBPH are classical methods; low light, side profiles, masks, and large pose changes reduce accuracy.", "The solution is designed for a single local camera and SQLite database, not a multi-classroom network deployment.", "The on-screen confidence percentage is a transformed LBPH distance, not a statistically calibrated probability.", "The simple local login should be strengthened for production use with password hashing and user management."])
    document.add_heading("Future Scope", level=2)
    add_bullets(document, ["Replace LBPH with a modern deep-learning face embedding model and liveness detection.", "Add multi-user roles, password hashing, audit logs, and encrypted backups.", "Synchronize attendance with an institution server or LMS through a secure API.", "Add course/class schedules, subject-wise attendance, charts, and absence alerts.", "Use a camera selection option and a responsive multi-camera deployment mode.", "Add consent forms, retention policies, and automatic deletion rules for biometric data."])
    document.add_heading("Deployment Recommendation", level=2)
    add_paragraph(document, "For a classroom demonstration, use a well-lit room, a fixed webcam, a small group of registered participants, and 70 varied face samples per participant. Retrain the model immediately after changing student records and verify the exported CSV before presenting results.")
    page_break(document)

    # 14 Conclusion/references
    document.add_heading("9. Conclusion", level=1)
    add_paragraph(document, "The Face Recognition Attendance System demonstrates a complete desktop workflow: secure entry, student registration, local dataset capture, LBPH training, real-time recognition, duplicate-safe attendance storage, record search, and CSV export. Separating GUI, database, capture, training, recognition, and reporting modules makes the code understandable for second-year students and easier to test or extend.")
    add_paragraph(document, "The project deliberately favors a practical, offline architecture that can run on a typical Windows laptop with Python and a webcam. Although the chosen recognition approach has limits, it provides a strong foundation for learning how computer vision components interact with a user interface and persistent data layer.")
    document.add_heading("References", level=1)
    add_numbered(document, [
        "OpenCV Documentation. Face Recognition with Local Binary Patterns Histograms (LBPH). https://docs.opencv.org/",
        "OpenCV Documentation. Cascade Classifier Detection. https://docs.opencv.org/",
        "Python Documentation. tkinter - Python interface to Tcl/Tk. https://docs.python.org/3/library/tkinter.html",
        "SQLite Documentation. SQLite is a self-contained SQL database engine. https://www.sqlite.org/docs.html",
    ])
    document.add_heading("Appendix: Project Files", level=2)
    add_paragraph(document, "The source folder contains main.py, login.py, register.py, train.py, recognize.py, attendance.py, database.py, and utils.py. Supporting folders hold the database, dataset, trained model, Haar cascade, CSV exports, test cases, and the diagram source files.")

    document.save(OUTPUT)
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    build_report()
