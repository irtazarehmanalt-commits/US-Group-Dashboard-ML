"""Audit log: a lightweight, best-effort activity trail per user. Visible only
to admins, from the Audit Log tab.
"""
from sqlalchemy import text
from chatbot.db import pg_engine


def log_action(email: str, name: str, action: str, details: str = "") -> None:
    """Record one action. Silently does nothing for an anonymous caller (no
    email to attribute it to) and silently swallows DB errors - audit logging
    is a side note to the real feature, never a reason for it to fail."""
    if not email:
        return
    try:
        with pg_engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO audit_log (user_email, user_name, action, details)
                    VALUES (:email, :name, :action, :details)
                """),
                {"email": email, "name": name, "action": action, "details": details},
            )
            conn.commit()
    except Exception as exc:
        print(f"[audit] failed to log '{action}' for {email}: {exc}")


def get_user_timeline(email: str, name: str, limit: int = 300) -> list[dict]:
    """Every recorded action for one user, most recent first. Merges the
    dedicated audit_log table with chat_history (which predates audit_log and
    only tracks the asker by name, not email), so chat questions show up in
    the same timeline as logins, predictions, reports, etc."""
    with pg_engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT action, details, created_at FROM (
                    SELECT action, details, created_at
                    FROM audit_log
                    WHERE user_email = :email
                    UNION ALL
                    SELECT 'chat' AS action, ('Asked: ' || question) AS details, created_at
                    FROM chat_history
                    WHERE user_name = :name
                ) combined
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"email": email, "name": name, "limit": limit},
        )
        return [dict(r._mapping) for r in rows]
