import html
import os
import random
import secrets
import string
from datetime import datetime, timedelta

import requests
from jose import jwt
from sqlalchemy import text
from chatbot.db import pg_engine
from audit import log_action
from mailer import send_email

SECRET_KEY = "change-this-to-something-random-later"  # fine for now, real app needs a proper secret
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

OTP_TTL_MINUTES = 10

# Optional public URL of the running app - when set, the approval email
# includes a "Log in" button. Left out entirely when unset (e.g. the app is
# only reachable at localhost) rather than shipping a button that goes nowhere.
APP_URL = os.getenv("APP_URL", "")

# Public Google OAuth client id (safe to expose to the frontend). Empty -> the
# "Continue with Google" button is hidden and /auth/google is disabled.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

pending_otps = {}  # temporary in-memory store: {email: {name, password, otp, expires}}

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

# --- Email templates (bodies only - mailer.send_email supplies the shared
# shell/Gmail plumbing) --------------------------------------------------

def send_otp_email(to_email: str, otp: str, name: str) -> bool:
    """Email a verification code from SMTP_EMAIL via the Gmail API. Returns False
    if Gmail OAuth isn't configured, so the caller can fall back to on-screen."""
    safe_name = html.escape(name)
    body_html = f"""\
<p style="margin:0 0 16px;">Hi {safe_name},</p>
<p style="margin:0 0 24px;">Use the code below to verify your email and finish creating your account.</p>
<div style="text-align:center;margin:0 0 24px;">
  <span style="display:inline-block;padding:14px 28px;background:#b8f7e4;color:#0b1f19;font-size:28px;font-weight:700;letter-spacing:8px;border-radius:10px;font-family:'Courier New',monospace;">{otp}</span>
</div>
<p style="margin:0 0 24px;color:#6b7280;font-size:13px;">This code expires in {OTP_TTL_MINUTES} minutes. If you didn't request this, you can safely ignore this email.</p>
<div style="border-top:1px solid #e5e7eb;padding-top:20px;">
  <p style="margin:0;">Once verified, your account will be <strong>submitted for admin approval</strong>. You'll get another email as soon as an administrator approves or rejects your request - you won't be able to log in until then.</p>
</div>
"""
    text_fallback = (
        f"Hi {name},\n\n"
        f"Your US Group verification code is: {otp}\n"
        f"It expires in {OTP_TTL_MINUTES} minutes.\n\n"
        f"Once verified, your account will be submitted for admin approval. "
        f"You'll get another email as soon as an administrator approves or rejects "
        f"your request - you won't be able to log in until then.\n\n"
        f"If you didn't request this, ignore this email."
    )
    return send_email(to_email, "Your US Group verification code", body_html, text_fallback)


def send_approval_email(to_email: str, name: str) -> bool:
    """Notify a user their account was approved. Best-effort - failures are the
    caller's problem to log, not to surface to the admin as a request failure."""
    safe_name = html.escape(name)
    login_button = (
        f'<div style="text-align:center;margin-top:24px;">'
        f'<a href="{APP_URL}" style="display:inline-block;padding:12px 28px;background:#0b1220;color:#b8f7e4;'
        f'text-decoration:none;font-weight:600;border-radius:8px;font-size:14px;">Log in</a></div>'
        if APP_URL else ""
    )
    body_html = f"""\
<p style="margin:0 0 16px;">Hi {safe_name},</p>
<p style="margin:0 0 16px;">
  <span style="display:inline-block;padding:4px 12px;background:#d1fae5;color:#065f46;border-radius:999px;font-size:13px;font-weight:600;">Approved</span>
</p>
<p style="margin:0;">An administrator has approved your account for the US Group Analytics Dashboard. You can now log in with the email and password you signed up with.</p>
{login_button}
"""
    text_fallback = (
        f"Hi {name},\n\n"
        f"Your account for the US Group Analytics Dashboard has been approved by an "
        f"administrator. You can now log in with the email and password you signed up with."
        + (f"\n\n{APP_URL}" if APP_URL else "")
    )
    return send_email(to_email, "Your US Group account has been approved", body_html, text_fallback)


def send_rejection_email(to_email: str, name: str) -> bool:
    """Notify a user their pending account request was rejected. Best-effort,
    same reasoning as send_approval_email."""
    safe_name = html.escape(name)
    body_html = f"""\
<p style="margin:0 0 16px;">Hi {safe_name},</p>
<p style="margin:0 0 16px;">
  <span style="display:inline-block;padding:4px 12px;background:#fee2e2;color:#991b1b;border-radius:999px;font-size:13px;font-weight:600;">Not approved</span>
</p>
<p style="margin:0;">An administrator has reviewed your account request for the US Group Analytics Dashboard and did not approve it. If you believe this is a mistake, please contact your administrator.</p>
"""
    text_fallback = (
        f"Hi {name},\n\n"
        f"Your account request for the US Group Analytics Dashboard was reviewed by an "
        f"administrator and was not approved. If you believe this is a mistake, please "
        f"contact your administrator."
    )
    return send_email(to_email, "Your US Group account request was not approved", body_html, text_fallback)

def start_signup(name: str, email: str, password: str) -> dict:
    otp = generate_otp()
    pending_otps[email] = {
        "name": name, "password": password, "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES),
    }
    try:
        emailed = send_otp_email(email, otp, name)
    except Exception as exc:
        print(f"[auth] OTP email failed for {email}: {exc}")
        emailed = False
    # When emailed, don't leak the code back to the client; otherwise return it
    # as a dev fallback so signup still works before SMTP is configured.
    return {"emailed": emailed, "otp": None if emailed else otp}

def verify_otp_and_create_account(email: str, entered_otp: str) -> bool:
    pending = pending_otps.get(email)
    if not pending or pending["otp"] != entered_otp:
        return False
    if datetime.utcnow() > pending["expires"]:
        del pending_otps[email]
        return False

    with pg_engine.connect() as conn:
        conn.execute(
            # is_approved defaults to FALSE - a new signup is pending until
            # an admin approves it from the Accounts screen
            text("INSERT INTO users (name, email, password) VALUES (:n, :e, :p)"),
            {"n": pending["name"], "e": email, "p": pending["password"]}
        )
        conn.commit()

    log_action(email, pending["name"], "signup", "Signed up")
    del pending_otps[email]
    return True

def login(email: str, password: str) -> dict:
    with pg_engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name, email, role, is_approved FROM users WHERE email = :e AND password = :p"),
            {"e": email, "p": password}
        )
        user = result.mappings().first()

    if not user:
        return None

    if not user["is_approved"]:
        return {"pending": True}

    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    log_action(user["email"], user["name"], "login", "Logged in")
    return {"token": token, "name": user["name"], "role": user["role"]}

def verify_user_password(email: str, password: str) -> bool:
    with pg_engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM users WHERE email = :e AND password = :p"),
            {"e": email, "p": password}
        )
        return result.first() is not None

def approve_user(user_id: int, admin_email: str = "", admin_name: str = "") -> bool:
    with pg_engine.connect() as conn:
        row = conn.execute(
            text("UPDATE users SET is_approved = TRUE WHERE id = :id RETURNING name, email"),
            {"id": user_id}
        ).mappings().first()
        conn.commit()
    if row is None:
        return False
    try:
        send_approval_email(row["email"], row["name"])
    except Exception as exc:
        print(f"[auth] approval email failed for {row['email']}: {exc}")
    log_action(admin_email, admin_name, "approve_user", f"Approved {row['name']} ({row['email']})")
    return True

def delete_user(user_id: int, admin_email: str = "", admin_name: str = "") -> bool:
    """Delete a user account (used for both 'reject pending request' and 'delete
    account'). Refuses to delete admin accounts so the dashboard can't be locked
    out. Returns False if the user doesn't exist, True if a row was deleted.

    Only sends a rejection email when the account was still pending - deleting
    an already-approved account later isn't the same thing as rejecting it, so
    that case stays silent. The admin's own action is still logged either way."""
    with pg_engine.connect() as conn:
        row = conn.execute(
            text("SELECT name, email, role, is_approved FROM users WHERE id = :id"), {"id": user_id}
        ).mappings().first()
        if row is None:
            return False
        if row["role"] == "admin":
            raise ValueError("Admin accounts can't be deleted.")
        result = conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        conn.commit()
    if result.rowcount > 0:
        was_pending = not row["is_approved"]
        if was_pending:
            try:
                send_rejection_email(row["email"], row["name"])
            except Exception as exc:
                print(f"[auth] rejection email failed for {row['email']}: {exc}")
        action = "reject_user" if was_pending else "delete_user"
        verb = "Rejected pending sign-up" if was_pending else "Deleted account"
        log_action(admin_email, admin_name, action, f"{verb}: {row['name']} ({row['email']})")
    return result.rowcount > 0

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None

def google_login(credential: str) -> dict:
    """Verify a Google Identity Services ID token and log the user in.

    Returns the same shape as login(): {token, name, role} for an approved user,
    {"pending": True} for a new or not-yet-approved account, or None if the token
    is invalid. New Google users are created as pending (admin must approve),
    matching the email-signup policy.
    """
    if not GOOGLE_CLIENT_ID:
        raise RuntimeError("Google sign-in is not configured on the server.")

    # Verify the ID token with Google and confirm it was issued for OUR client.
    try:
        resp = requests.get("https://oauth2.googleapis.com/tokeninfo",
                            params={"id_token": credential}, timeout=10)
    except Exception:
        return None
    if resp.status_code != 200:
        return None
    info = resp.json()
    if info.get("aud") != GOOGLE_CLIENT_ID:
        return None
    if str(info.get("email_verified")).lower() != "true":
        return None

    email = info.get("email")
    name = info.get("name") or (email.split("@")[0] if email else "User")
    if not email:
        return None

    with pg_engine.connect() as conn:
        user = conn.execute(
            text("SELECT id, name, role, is_approved FROM users WHERE email = :e"),
            {"e": email},
        ).mappings().first()

        if user is None:
            # First time this Google account signs in -> create as pending. The
            # random password can't be used for password login (Google-only user).
            conn.execute(
                text("INSERT INTO users (name, email, password) VALUES (:n, :e, :p)"),
                {"n": name, "e": email, "p": "google:" + secrets.token_hex(16)},
            )
            conn.commit()
            log_action(email, name, "signup", "Signed up with Google")
            return {"pending": True}

    if not user["is_approved"]:
        return {"pending": True}

    payload = {
        "user_id": user["id"],
        "email": email,
        "name": user["name"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    log_action(email, user["name"], "login", "Logged in with Google")
    return {"token": token, "name": user["name"], "role": user["role"]}