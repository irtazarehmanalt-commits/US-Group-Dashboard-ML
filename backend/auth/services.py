import base64
import os
import random
import secrets
import string
from datetime import datetime, timedelta
from email.message import EmailMessage

import requests
from jose import jwt
from sqlalchemy import text
from chatbot.db import pg_engine

SECRET_KEY = "change-this-to-something-random-later"  # fine for now, real app needs a proper secret
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# --- OTP email (Gmail API over HTTPS) config ---
# We send via the Gmail REST API, NOT SMTP: this network blocks SMTP ports
# (465/587), but HTTPS/443 is open. Requires a one-time OAuth refresh token for
# the sender account with the gmail.send scope - run auth/gmail_oauth_setup.py to
# obtain GMAIL_REFRESH_TOKEN. If any of the three are missing, send_otp_email()
# returns False and the caller falls back to showing the code on screen.
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "irtazaworks123@gmail.com")  # the "From" address
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")
OTP_TTL_MINUTES = 10

# Public Google OAuth client id (safe to expose to the frontend). Empty -> the
# "Continue with Google" button is hidden and /auth/google is disabled.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

pending_otps = {}  # temporary in-memory store: {email: {name, password, otp, expires}}

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

def _gmail_access_token() -> str:
    """Exchange the long-lived refresh token for a short-lived access token."""
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GMAIL_CLIENT_ID,
        "client_secret": GMAIL_CLIENT_SECRET,
        "refresh_token": GMAIL_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]

def send_otp_email(to_email: str, otp: str) -> bool:
    """Email a verification code from SMTP_EMAIL via the Gmail API. Returns False
    if Gmail OAuth isn't configured, so the caller can fall back to on-screen."""
    if not (GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN):
        return False
    access_token = _gmail_access_token()
    msg = EmailMessage()
    msg["Subject"] = "Your US Group verification code"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg.set_content(
        f"Your US Group verification code is: {otp}\n\n"
        f"It expires in {OTP_TTL_MINUTES} minutes. If you didn't request this, ignore this email."
    )
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    resp = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": raw}, timeout=15,
    )
    resp.raise_for_status()
    return True

def start_signup(name: str, email: str, password: str) -> dict:
    otp = generate_otp()
    pending_otps[email] = {
        "name": name, "password": password, "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES),
    }
    try:
        emailed = send_otp_email(email, otp)
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

    return {"token": token, "name": user["name"], "role": user["role"]}

def verify_user_password(email: str, password: str) -> bool:
    with pg_engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM users WHERE email = :e AND password = :p"),
            {"e": email, "p": password}
        )
        return result.first() is not None

def approve_user(user_id: int) -> bool:
    with pg_engine.connect() as conn:
        result = conn.execute(
            text("UPDATE users SET is_approved = TRUE WHERE id = :id"),
            {"id": user_id}
        )
        conn.commit()
    return result.rowcount > 0

def delete_user(user_id: int) -> bool:
    """Delete a user account (used for both 'reject pending request' and 'delete
    account'). Refuses to delete admin accounts so the dashboard can't be locked
    out. Returns False if the user doesn't exist, True if a row was deleted."""
    with pg_engine.connect() as conn:
        row = conn.execute(
            text("SELECT role FROM users WHERE id = :id"), {"id": user_id}
        ).mappings().first()
        if row is None:
            return False
        if row["role"] == "admin":
            raise ValueError("Admin accounts can't be deleted.")
        result = conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        conn.commit()
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
    return {"token": token, "name": user["name"], "role": user["role"]}