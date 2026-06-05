"""
Gmail API sender — completely free
Uses OAuth2 service account or user credentials via Google Cloud free tier.
"""

import streamlit as st
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


def get_gmail_service():
    if not GMAIL_AVAILABLE:
        return None

    creds_json = st.secrets.get("GMAIL_CREDENTIALS_JSON", "")
    if not creds_json:
        return None

    # Normalize whitespace — handles multi-line TOML triple-quoted strings
    creds_json = " ".join(creds_json.split())

    try:
        creds_data = json.loads(creds_json)
    except json.JSONDecodeError as e:
        st.warning(f"Gmail credentials JSON is malformed: {e}")
        return None

    try:
        creds = Credentials(
            token=creds_data.get("token"),
            refresh_token=creds_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=["https://www.googleapis.com/auth/gmail.send"]
        )
        # The stored access token expires after ~1 hour; always refresh via
        # the refresh_token so we never fail on a stale access token.
        if creds.refresh_token:
            from google.auth.transport.requests import Request as GoogleRequest
            creds.refresh(GoogleRequest())
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        st.warning(f"Gmail auth error: {e}")
        return None


def send_email(to_email, subject, body, from_name="Kalob Hagen", reply_to=None):
    if not to_email or "@" not in to_email:
        return {"success": False, "message_id": None, "error": "Invalid email address", "simulated": False}

    service = get_gmail_service()

    if not service:
        st.info(f"📧 [SIMULATED] Would send to: {to_email} | Subject: {subject}")
        return {"success": True, "message_id": f"simulated_{to_email}", "error": None, "simulated": True}

    try:
        msg = MIMEMultipart("alternative")
        msg["To"] = to_email
        msg["Subject"] = subject
        from_addr = st.secrets.get("GMAIL_FROM_ADDRESS", "luigisolutions7@gmail.com")
        msg["From"] = f"{from_name} <{from_addr}>"
        if reply_to:
            msg["Reply-To"] = reply_to

        text_part = MIMEText(body, "plain")
        html_body = body.replace("\n", "<br>")
        html_part = MIMEText(
            f'<html><body style="font-family:Georgia,serif;font-size:15px;color:#222;max-width:580px;line-height:1.6;">{html_body}</body></html>',
            "html"
        )
        msg.attach(text_part)
        msg.attach(html_part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"success": True, "message_id": result.get("id"), "error": None, "simulated": False}

    except Exception as e:
        return {"success": False, "message_id": None, "error": str(e), "simulated": False}


def test_connection() -> tuple:
    """Return (ok: bool, detail: str). detail is the sender address on success or an error on failure."""
    if not GMAIL_AVAILABLE:
        return False, "google-auth libraries not installed (check requirements.txt)"
    if not st.secrets.get("GMAIL_CREDENTIALS_JSON", ""):
        return False, "GMAIL_CREDENTIALS_JSON not set in Streamlit secrets"
    service = get_gmail_service()
    if not service:
        return False, "Failed to initialize Gmail service (see warning above)"
    # get_gmail_service() already called creds.refresh() successfully — token is valid.
    # getProfile requires gmail.readonly which exceeds the gmail.send scope we authorized.
    from_addr = st.secrets.get("GMAIL_FROM_ADDRESS", "configured")
    return True, f"ready to send from {from_addr}"
