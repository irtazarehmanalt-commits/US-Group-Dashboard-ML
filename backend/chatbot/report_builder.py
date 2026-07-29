import pandas as pd
from .report_sections import get_report_sections
from .chart_generator import generate_chart
from .answer_generator import generate_natural_answer

def build_report_data() -> list[dict]:
    """Builds each section's chart + a short narrative summary.
    Returns a list ready to (a) stream to chat one-by-one, 
    (b) hand to the PDF assembler."""

    sections = get_report_sections()
    built_sections = []

    for section in sections:
        rows = section["data"]

        chart_image = generate_chart(rows)

        summary_prompt = f"Summarize this data in one short sentence for a business report titled '{section['title']}'"
        summary = generate_natural_answer(summary_prompt, rows)

        built_sections.append({
            "title": section["title"],
            "summary": summary,
            "chart_image_base64": chart_image,
            "data": rows
        })

    return built_sections