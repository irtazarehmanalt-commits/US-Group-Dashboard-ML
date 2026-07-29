import os
from ollama import Client
# added PRODUCTS_SCHEMA so the model can also query the scraped_products table
from .db import ORDERS_SCHEMA, PRODUCTS_SCHEMA

client = Client(
    host='https://ollama.com',
    headers={'Authorization': 'Bearer ' + os.getenv('OLAMA_API_KEY')}
)

def _history_block(history) -> str:
    """Render the last few conversation turns as a plain-text context block so
    the model can resolve follow-up references like 'it' / 'that product'. Kept
    as text inside the user message (rather than real chat turns) so the model
    doesn't drift back into natural-language replies instead of emitting SQL."""
    if not history:
        return ""
    lines = []
    for turn in history[-6:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role and content:
            who = "User" if role == "user" else "Assistant"
            lines.append(f"{who}: {content}")
    if not lines:
        return ""
    return ("Recent conversation (context only - use it to resolve references "
            "like 'it' or 'that product'):\n" + "\n".join(lines) + "\n\n")


def generate_sql(question: str, history=None) -> str:
    # The model sees both schemas. It should pick the orders table for US Group's
    # internal data and scraped_products for external retail-brand pricing, per
    # the guidance inside each schema block. Recent turns are prepended so
    # follow-up questions resolve correctly.
    response = client.chat(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "system", "content": f"You write PostgreSQL SELECT queries only. "
                                            f"You have two tables available.\n\n{ORDERS_SCHEMA}\n\n{PRODUCTS_SCHEMA}\n"
                                            f"Return ONLY the raw SQL, no markdown, no backticks, no explanation."},
            {"role": "user", "content": _history_block(history) + f"Current question: {question}"}
        ]
    )
    return response.message.content.strip()


def fix_sql(question: str, bad_sql: str, error: str, history=None) -> str:
    """Self-correction: given a query that failed and the database error, ask the
    model to return a corrected SELECT. Called once by ask_chatbot before giving
    up, so a single bad column name / syntax slip doesn't fail the whole turn."""
    user = (_history_block(history) +
            f"This PostgreSQL query failed:\n{bad_sql}\n\n"
            f"Database error:\n{error}\n\n"
            f"Original question: {question}\n"
            f"Return a corrected PostgreSQL SELECT query.")
    response = client.chat(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "system", "content": f"You fix broken PostgreSQL SELECT queries. "
                                            f"Tables available:\n\n{ORDERS_SCHEMA}\n\n{PRODUCTS_SCHEMA}\n"
                                            f"Return ONLY the corrected raw SQL, no markdown, no backticks, no explanation."},
            {"role": "user", "content": user}
        ]
    )
    return response.message.content.strip()