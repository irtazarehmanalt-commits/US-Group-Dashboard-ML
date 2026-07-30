"""Formal warning letters: an admin picks flagged audit-log actions for a
user, an LLM drafts a letter from that context (admin can edit before
sending), then it's saved (visible to the user on their own Warnings tab)
and optionally emailed.

Named user_warnings, not warnings - a top-level warnings.py would shadow
Python's stdlib `warnings` module, which pandas/numpy/sklearn call into
constantly (e.g. warnings.filterwarnings), and breaks them in confusing ways.
"""
import html
import io
import json
import os
from datetime import datetime
from pathlib import Path

from ollama import Client
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter as PAGE_SIZE
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import text

from chatbot.db import pg_engine
from mailer import send_email

# Same letterhead assets/positions as chatbot/custom_report.py, so a warning
# letter and the standard analytics report look like they come from the same
# company, just with a different top-right label.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
LION_LOGO = FRONTEND_DIR / "logo-lion.png"
WORDMARK_LOGO = FRONTEND_DIR / "logo-wordmark.png"
_GRAPHITE = colors.HexColor('#25272C')
_RULE_COLOR = colors.HexColor('#dddddd')
_STAMP_COLOR = colors.HexColor('#0f7a5c')  # same accent as the standard report

_client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.getenv("OLAMA_API_KEY", "")},
)

_SYSTEM_PROMPT = """\
You draft official written warning letters on behalf of US Group, a Pakistani \
textile and apparel manufacturing company (denim fabric, denim garments, \
twill garments, footwear, lifestyle apparel), addressed to a user of its \
internal analytics dashboard.

You are given a list of specific flagged actions an administrator selected \
from that user's activity log. Write a formal, professional warning letter:

- Standard business-letter structure: a "US GROUP" letterhead line, the date, \
"To: [Name]", a subject line, a salutation ("Dear [Name],"), body paragraphs, \
a closing, and a signature block signed by the issuer.
- Reference the flagged actions specifically but paraphrase them \
professionally - do not dump raw log lines verbatim.
- Explain why this is a concern and state plainly that it must not continue.
- Note that continued violations may lead to further action, without \
inventing specific disciplinary policies you were not given.
- Firm but respectful, HR-appropriate tone. No casual language, no emojis, \
no markdown formatting.
- Output ONLY the letter text - no preamble, no explanation, no markdown \
fences.
"""


def generate_warning_letter(user_name: str, admin_name: str, actions: list[dict]) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    action_lines = "\n".join(
        f"- [{a.get('created_at', '')}] {a.get('action', '')}: {a.get('details', '')}"
        for a in actions
    )
    user_prompt = (
        f"Employee name: {user_name}\n"
        f"Date: {today}\n"
        f"Issued by: {admin_name or 'US Group Administration'}\n\n"
        f"Flagged actions:\n{action_lines}\n\n"
        f"Write the warning letter now."
    )
    response = _client.chat(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.message.content.strip()


def create_warning(user_email: str, user_name: str, letter: str, actions: list[dict],
                    admin_email: str, admin_name: str, emailed: bool) -> int:
    with pg_engine.connect() as conn:
        row = conn.execute(
            text("""
                INSERT INTO warnings (user_email, user_name, letter, actions_context,
                                       issued_by_email, issued_by_name, emailed)
                VALUES (:user_email, :user_name, :letter, :actions_context,
                        :admin_email, :admin_name, :emailed)
                RETURNING id
            """),
            {
                "user_email": user_email, "user_name": user_name, "letter": letter,
                "actions_context": json.dumps(actions),
                "admin_email": admin_email, "admin_name": admin_name, "emailed": emailed,
            },
        ).mappings().first()
        conn.commit()
    return row["id"]


def get_warnings_for_user(email: str) -> list[dict]:
    with pg_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, letter, emailed, created_at FROM warnings "
                 "WHERE user_email = :email ORDER BY created_at DESC"),
            {"email": email},
        )
        return [dict(r._mapping) for r in rows]


def get_all_sent_warnings() -> list[dict]:
    """Every warning ever issued, across all recipients - the admin side of
    this feature ('Warnings Sent'), since no one sends the admin a warning."""
    with pg_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, user_email, user_name, letter, emailed, "
                 "issued_by_name, issued_by_email, created_at "
                 "FROM warnings ORDER BY created_at DESC")
        )
        return [dict(r._mapping) for r in rows]


def send_warning_email(to_email: str, letter: str) -> bool:
    # Preserve the letter's paragraph breaks in the HTML version. The letter
    # itself already opens with "Dear [Name]," so no separate greeting here.
    paragraphs = [html.escape(p).replace("\n", "<br>") for p in letter.split("\n\n")]
    letter_html = "<br><br>".join(paragraphs)
    body_html = f'<div style="white-space:normal;">{letter_html}</div>'
    return send_email(to_email, "Official Notice from US Group", body_html, letter)


def _draw_letter_header_footer(canvas, doc):
    """Same header/footer treatment as the standard report PDF (logo, rule,
    dated footer with page number) - just labeled for a formal notice instead
    of an analytics report."""
    canvas.saveState()
    page_width, page_height = PAGE_SIZE

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
    canvas.drawRightString(page_width - 0.7 * inch, header_baseline, "Official Notice")

    canvas.setStrokeColor(_RULE_COLOR)
    canvas.setLineWidth(0.75)
    canvas.line(0.7 * inch, page_height - 0.85 * inch, page_width - 0.7 * inch, page_height - 0.85 * inch)

    canvas.line(0.7 * inch, 0.65 * inch, page_width - 0.7 * inch, 0.65 * inch)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(0.7 * inch, 0.45 * inch, f"US Group · Generated {datetime.now().strftime('%B %d, %Y')}")
    canvas.drawRightString(page_width - 0.7 * inch, 0.45 * inch, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()


# LLM output sometimes includes punctuation outside reportlab's default font
# encoding (WinAnsi) - e.g. a non-breaking hyphen instead of a plain "-" in a
# compound word. Those render as a solid glyph-missing box, so normalize the
# risky ones to plain ASCII before they ever reach a Paragraph.
_PDF_UNSAFE_CHARS = {
    "‐": "-", "‑": "-", "‒": "-", "―": "-",
    "­": "", "⁠": "", "﻿": "",
}


def _sanitize_for_pdf(text: str) -> str:
    for bad, good in _PDF_UNSAFE_CHARS.items():
        text = text.replace(bad, good)
    return text


class _AdminStampFlowable(Flowable):
    """A round, semi-transparent 'official' stamp, drawn at a slight angle
    like a real ink stamp - placed after the signature block, right-aligned
    so it reads as a stamp next to the signature rather than a random shape."""

    def __init__(self, date_str: str, size: float = 1.5 * inch):
        super().__init__()
        self.date_str = date_str
        self.size = size
        self.hAlign = 'RIGHT'

    def wrap(self, avail_width, avail_height):
        return (self.size, self.size)

    def draw(self):
        c = self.canv
        c.saveState()
        c.translate(self.size / 2, self.size / 2)
        c.rotate(-9)
        c.setFillAlpha(0.75)
        c.setStrokeAlpha(0.75)
        c.setStrokeColor(_STAMP_COLOR)
        c.setFillColor(_STAMP_COLOR)

        radius = self.size / 2 - 3
        c.setLineWidth(2.2)
        c.circle(0, 0, radius, stroke=1, fill=0)
        c.setLineWidth(1)
        c.circle(0, 0, radius - 7, stroke=1, fill=0)

        c.setFont('Helvetica-Bold', 12)
        c.drawCentredString(0, radius - 28, "US GROUP")

        c.setLineWidth(0.8)
        c.line(-radius + 26, radius - 36, radius - 26, radius - 36)

        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(0, 4, "OFFICIALLY")
        c.drawCentredString(0, -11, "AUTHORIZED")

        c.line(-radius + 26, -radius + 32, radius - 26, -radius + 32)
        c.setFont('Helvetica', 8)
        c.drawCentredString(0, -radius + 17, self.date_str)

        c.restoreState()


def build_warning_pdf(letter: str) -> bytes:
    """Render a warning letter (admin draft or an already-saved one) as a PDF
    with the same letterhead as the standard analytics report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        topMargin=1.1 * inch, bottomMargin=0.9 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle('Body', parent=styles['BodyText'],
                                 fontSize=11, leading=17, spaceBefore=10, textColor=_GRAPHITE)

    story = []
    for para in letter.split("\n\n"):
        cleaned = _sanitize_for_pdf(para.strip())
        if not cleaned:
            continue
        story.append(Paragraph(html.escape(cleaned).replace("\n", "<br/>"), body_style))

    # Official-looking stamp under the signature, right-aligned so it reads
    # as "stamped next to the signature" rather than a floating shape.
    story.append(Spacer(1, 0.1 * inch))
    story.append(_AdminStampFlowable(datetime.now().strftime("%B %d, %Y")))

    doc.build(story, onFirstPage=_draw_letter_header_footer, onLaterPages=_draw_letter_header_footer)
    buffer.seek(0)
    return buffer.read()
