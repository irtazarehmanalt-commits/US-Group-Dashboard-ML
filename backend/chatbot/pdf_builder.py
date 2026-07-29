import base64
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def build_pdf(sections: list[dict]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("US Group — Analytics Report", styles['Title']))
    story.append(Spacer(1, 0.3 * inch))

    for section in sections:
        story.append(Paragraph(section["title"], styles['Heading2']))
        story.append(Paragraph(section["summary"], styles['BodyText']))
        story.append(Spacer(1, 0.1 * inch))

        if section["chart_image_base64"]:
            image_bytes = base64.b64decode(section["chart_image_base64"])
            image_buffer = io.BytesIO(image_bytes)
            story.append(Image(image_buffer, width=5.5 * inch, height=3.4 * inch))

        story.append(Spacer(1, 0.4 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()