from sqlalchemy import text
from .sql_generator import generate_sql, fix_sql
from .safety import is_safe_sql
from .db import run_sql, pg_engine
from .answer_generator import generate_natural_answer
from .date_resolver import resolve_relative_dates

def save_to_history(question: str, answer: str, user_name: str = None):
    with pg_engine.connect() as conn:
        conn.execute(
            text("INSERT INTO chat_history (question, answer, user_name) VALUES (:q, :a, :u)"),
            {"q": question, "a": answer, "u": user_name}
        )
        conn.commit()

def _is_chartable(rows) -> bool:
    """A result is worth charting when it has at least two comparable rows
    (e.g. one per sub-company/payment term/month) and at least one numeric
    column to plot alongside the label column."""
    if not rows or len(rows) < 2:
        return False
    first = rows[0]
    if not isinstance(first, dict) or len(first) < 2:
        return False
    return any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in list(first.values())[1:])

def ask_chatbot(question: str, user_name: str = None, history=None) -> dict:
    resolved_question = resolve_relative_dates(question)
    sql = generate_sql(resolved_question, history=history)

    if not is_safe_sql(sql):
        answer = "That question can't be processed for safety reasons."
        save_to_history(question, answer, user_name)
        return {"answer": answer, "sql": None, "data": None, "can_chart": False}

    try:
        rows = run_sql(sql)
    except Exception as e:
        # Self-correct once: hand the failing query + DB error back to the model
        # so a single bad column/syntax slip doesn't fail the whole turn.
        try:
            fixed = fix_sql(resolved_question, sql, str(e), history=history)
        except Exception:
            fixed = None
        if not fixed or not is_safe_sql(fixed):
            answer = f"I couldn't run that query: {str(e)}"
            save_to_history(question, answer, user_name)
            return {"answer": answer, "sql": sql, "data": None, "can_chart": False}
        sql = fixed
        try:
            rows = run_sql(sql)
        except Exception as e2:
            answer = f"I couldn't run that query: {str(e2)}"
            save_to_history(question, answer, user_name)
            return {"answer": answer, "sql": sql, "data": None, "can_chart": False}

    answer = generate_natural_answer(question, rows)
    save_to_history(question, answer, user_name)

    return {"answer": answer, "sql": sql, "data": rows, "can_chart": _is_chartable(rows)}