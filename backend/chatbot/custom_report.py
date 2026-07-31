import base64
import io
import os
from ollama import Client
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

GRAPHITE = colors.HexColor('#25272C')
ACCENT = colors.HexColor('#0f7a5c')
RULE_COLOR = colors.HexColor('#dddddd')

# Cloud, not local - see chatbot/answer_generator.py for why.
client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.getenv("OLAMA_API_KEY", "")},
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
LION_LOGO = FRONTEND_DIR / "logo-lion.png"
WORDMARK_LOGO = FRONTEND_DIR / "logo-wordmark.png"


def _draw_header_footer(canvas, doc):
    """Runs on every page (see doc.build below) - draws the logo, a page
    label, and a footer directly on the canvas, outside the normal flowable
    story, so it repeats identically no matter how many pages the report is."""
    canvas.saveState()
    page_width, page_height = letter

    # --- Header: lion + wordmark top-left, section label top-right ---
    header_baseline = page_height - 0.6 * inch
    if LION_LOGO.exists():
        canvas.drawImage(
            str(LION_LOGO), 0.7 * inch, header_baseline - 0.08 * inch,
            width=0.3 * inch, height=0.3 * inch,
            mask='auto', preserveAspectRatio=True, anchor='sw',
        )
    if WORDMARK_LOGO.exists():
        canvas.drawImage(
            str(WORDMARK_LOGO), 1.1 * inch, header_baseline - 0.02 * inch,
            width=1.3 * inch, height=0.22 * inch,
            mask='auto', preserveAspectRatio=True, anchor='sw',
        )

    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(page_width - 0.7 * inch, header_baseline, "Analytics Report")

    canvas.setStrokeColor(RULE_COLOR)
    canvas.setLineWidth(0.75)
    canvas.line(0.7 * inch, page_height - 0.85 * inch, page_width - 0.7 * inch, page_height - 0.85 * inch)

    # --- Footer: generation date left, page number right ---
    canvas.line(0.7 * inch, 0.65 * inch, page_width - 0.7 * inch, 0.65 * inch)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(0.7 * inch, 0.45 * inch, f"US Group · Generated {datetime.now().strftime('%B %d, %Y')}")
    canvas.drawRightString(page_width - 0.7 * inch, 0.45 * inch, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()


def write_report_paragraph(question: str, answer: str) -> str:
    response = client.chat(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "user", "content":
                f"Rewrite this as a single polished, professional business-report "
                f"paragraph (no headings, no bullet points, 2-3 sentences). "
                f"Original question: {question}\nOriginal finding: {answer}"}
        ]
    )
    return response.message.content.strip()


def build_custom_report_pdf(selected_charts: list[dict]) -> bytes:
    """selected_charts: list of {question, answer, chart_image_base64}"""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.1 * inch, bottomMargin=0.9 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()

    section_title_style = ParagraphStyle('SectionTitle', parent=styles['Heading2'],
                                          fontSize=15, textColor=GRAPHITE, spaceBefore=10)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'],
                                 fontSize=10.5, leading=16, spaceBefore=6)

    story = []

    for i, item in enumerate(selected_charts, 1):
        paragraph = write_report_paragraph(item["question"], item["answer"])

        story.append(Paragraph(f"{i}. {item['question']}", section_title_style))
        story.append(Paragraph(paragraph, body_style))
        story.append(Spacer(1, 0.15 * inch))

        if item.get("chart_image_base64"):
            image_bytes = base64.b64decode(item["chart_image_base64"])
            image_buffer = io.BytesIO(image_bytes)
            story.append(Image(image_buffer, width=5.8 * inch, height=3.6 * inch))

        story.append(Spacer(1, 0.35 * inch))

    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)
    buffer.seek(0)
    return buffer.read()
