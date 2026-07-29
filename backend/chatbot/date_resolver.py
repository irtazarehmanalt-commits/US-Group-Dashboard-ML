from .db import run_sql

def resolve_relative_dates(question: str) -> str:
    """Rewrites vague date phrases into concrete Year/Month values,
    computed directly from the database — before the LLM ever sees them."""

    latest = run_sql('SELECT "Year", "Month" FROM orders ORDER BY "Year" DESC, "Month" DESC LIMIT 1')
    latest_year, latest_month = latest[0]['Year'], latest[0]['Month']

    last_month = latest_month - 1
    last_month_year = latest_year
    if last_month == 0:
        last_month = 12
        last_month_year -= 1

    q = question.lower()

    if "last month" in q:
        question += f" (Note: 'last month' means Year = {last_month_year} AND Month = {last_month})"
    elif "this month" in q or "current month" in q:
        question += f" (Note: 'this month' means Year = {latest_year} AND Month = {latest_month})"
    elif "this year" in q or "current year" in q:
        question += f" (Note: 'this year' means Year = {latest_year})"
    elif "last year" in q:
        question += f" (Note: 'last year' means Year = {latest_year - 1})"

    return question