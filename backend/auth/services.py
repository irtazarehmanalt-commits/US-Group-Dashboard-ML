import base64
import html
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

# --- Email templates -------------------------------------------------------
# One shared HTML shell (header/footer chrome, matches the dashboard's dark
# navy + mint accent look) so the three emails below only supply their inner
# content. Table-based layout + inline styles because email clients ignore
# <style> blocks and modern CSS.

def _email_shell(body_html: str) -> str:
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#eef1f5;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f5;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 8px 24px rgba(15,23,42,0.08);">
            <tr>
              <td style="background:#0b1220;padding:24px 32px;">
                <span style="color:#b8f7e4;font-size:20px;font-weight:700;letter-spacing:0.5px;">US GROUP</span>
                <div style="color:#9aa0ac;font-size:12px;margin-top:2px;">Analytics Dashboard</div>
              </td>
            </tr>
            <tr>
              <td style="padding:32px;color:#1f2937;font-size:15px;line-height:1.6;">
                {body_html}
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px;background:#f7f8fa;color:#9aa0ac;font-size:12px;">
                This is an automated message from the US Group Analytics Dashboard. Please don't reply to this email.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def _send_email(to_email: str, subject: str, body_html: str, text_fallback: str) -> bool:
    """Send one HTML email (with a plain-text fallback part) from SMTP_EMAIL via
    the Gmail API. Returns False if Gmail OAuth isn't configured - callers decide
    what that means for them (OTP falls back to on-screen; approval/rejection
    just skip silently, since account creation shouldn't hinge on notification
    delivery)."""
    if not (GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN):
        return False
    access_token = _gmail_access_token()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg.set_content(text_fallback)
    msg.add_alternative(_email_shell(body_html), subtype="html")
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    resp = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": raw}, timeout=15,
    )
    resp.raise_for_status()
    return True


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
    return _send_email(to_email, "Your US Group verification code", body_html, text_fallback)


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
    return _send_email(to_email, "Your US Group account has been approved", body_html, text_fallback)


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
    return _send_email(to_email, "Your US Group account request was not approved", body_html, text_fallback)

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
    return True

def delete_user(user_id: int) -> bool:
    """Delete a user account (used for both 'reject pending request' and 'delete
    account'). Refuses to delete admin accounts so the dashboard can't be locked
    out. Returns False if the user doesn't exist, True if a row was deleted.

    Only sends a rejection email when the account was still pending - deleting
    an already-approved account later isn't the same thing as rejecting it, so
    that case stays silent."""
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
    if result.rowcount > 0 and not row["is_approved"]:
        try:
            send_rejection_email(row["email"], row["name"])
        except Exception as exc:
            print(f"[auth] rejection email failed for {row['email']}: {exc}")
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