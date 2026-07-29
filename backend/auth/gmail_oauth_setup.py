"""One-time helper: obtain a Gmail API refresh token for sending OTP emails.

Why: this network blocks SMTP ports, so we send OTPs via the Gmail REST API over
HTTPS instead. That needs a long-lived refresh token for the sender account.

Run ONCE, from the backend folder:
    venv\\Scripts\\python.exe auth\\gmail_oauth_setup.py

Prerequisites (in backend/.env):
    GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET  -> from a Google Cloud OAuth client of
    type "Desktop app", in a project where the Gmail API is enabled, and whose
    OAuth consent screen lists irtazaworks123@gmail.com as a test user (or is
    Internal). Scope requested: gmail.send.

It opens a browser, you consent as irtazaworks123@gmail.com, and it prints the
line to paste into .env:  GMAIL_REFRESH_TOKEN=...
"""
import http.server
import sys
import urllib.parse
import webbrowser

import requests
from dotenv import load_dotenv
import os

load_dotenv()
CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
PORT = 8765
REDIRECT_URI = f"http://localhost:{PORT}/"
SCOPE = "https://www.googleapis.com/auth/gmail.send"

_result = {}


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params or "error" in params:
            _result["code"] = params.get("code", [None])[0]
            _result["error"] = params.get("error", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Done - you can close this tab and return to the terminal.</h2>")

    def log_message(self, *args):
        pass  # keep the console clean


def main():
    if not (CLIENT_ID and CLIENT_SECRET):
        print("ERROR: set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in backend/.env first.")
        sys.exit(1)

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",   # ask for a refresh token
        "prompt": "consent",        # force a refresh token even on re-consent
    })

    server = http.server.HTTPServer(("localhost", PORT), _Handler)
    print("A browser window will open. Log in as irtazaworks123@gmail.com and click Allow.")
    print("If it doesn't open, paste this URL into your browser:\n")
    print(auth_url, "\n")
    webbrowser.open(auth_url)

    # handle requests until we capture the code (ignores e.g. a favicon hit)
    while "code" not in _result and "error" not in _result:
        server.handle_request()

    if _result.get("error") or not _result.get("code"):
        print("Authorization failed:", _result.get("error") or "no code returned")
        sys.exit(1)

    tokens = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": _result["code"],
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }, timeout=15).json()

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("No refresh token returned. Full response:", tokens)
        print("Tip: revoke prior access at https://myaccount.google.com/permissions and re-run.")
        sys.exit(1)

    print("\n=== SUCCESS ===")
    print("Paste this line into backend/.env, then restart the server:\n")
    print(f"GMAIL_REFRESH_TOKEN={refresh_token}\n")


if __name__ == "__main__":
    main()
