"""Shared outbound email (Gmail API over HTTPS, not SMTP - this network blocks
SMTP ports 465/587, but HTTPS/443 is open). Requires a one-time OAuth refresh
token for the sender account with the gmail.send scope - run
auth/gmail_oauth_setup.py to obtain GMAIL_REFRESH_TOKEN.

Used by auth/services.py (OTP, approval, rejection emails) and
user_warnings.py (warning-letter emails) - one Gmail client, one HTML shell,
so every outgoing email looks consistent.
"""
import base64
import os
from email.message import EmailMessage

import requests

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "irtazaworks123@gmail.com")  # the "From" address
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")


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


# Shared HTML wrapper (header/footer chrome, matches the dashboard's dark navy
# + mint accent look) so every email template only supplies its inner content.
# Table-based layout + inline styles because email clients ignore <style>
# blocks and modern CSS.
def email_shell(body_html: str) -> str:
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


def send_email(to_email: str, subject: str, body_html: str, text_fallback: str) -> bool:
    """Send one HTML email (with a plain-text fallback part) from SMTP_EMAIL via
    the Gmail API. Returns False if Gmail OAuth isn't configured - callers decide
    what that means for them (OTP falls back to on-screen; other emails just
    skip silently, since the triggering action shouldn't hinge on notification
    delivery)."""
    if not (GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN):
        return False
    access_token = _gmail_access_token()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg.set_content(text_fallback)
    msg.add_alternative(email_shell(body_html), subtype="html")
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    resp = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": raw}, timeout=15,
    )
    resp.raise_for_status()
    return True
