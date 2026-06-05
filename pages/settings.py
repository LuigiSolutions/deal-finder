import streamlit as st


def render():
    st.markdown('<div class="section-title">⚙️ Settings & Setup Guide</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔑 API Keys", "📋 Setup Guide", "🧪 Test Connections"])

    with tab1:
        st.markdown("""
        <div class="info-box">
        These keys go in your Streamlit <code>secrets.toml</code> file (local) or in
        <strong>Streamlit Cloud → App Settings → Secrets</strong> (deployed).
        Never commit secrets to GitHub.
        </div>
        """, unsafe_allow_html=True)

        st.code("""
# .streamlit/secrets.toml

# Your name (used in email signatures)
YOUR_NAME = "Kalob Hagen"

# ── FREE: Gemini Flash AI ──────────────────────────────────
# Get free key at: https://aistudio.google.com/app/apikey
# Free tier: 15 req/min, 1M tokens/day — more than enough
GEMINI_API_KEY = "AIza..."

# ── FREE: Supabase Database ───────────────────────────────
# Create free project at: https://supabase.com
# Get from: Project Settings → API → URL + anon key
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJ..."

# ── FREE: Gmail API ───────────────────────────────────────
# Setup guide below. Paste the JSON as a single line string.
GMAIL_CREDENTIALS_JSON = '{"token":"ya29...","refresh_token":"1//...","client_id":"...","client_secret":"..."}'
GMAIL_FROM_ADDRESS = "luigisolutions7@gmail.com"
        """, language="toml")

    with tab2:
        st.markdown('<div class="section-title" style="font-size:1.1rem;">Step-by-Step Setup (All Free)</div>', unsafe_allow_html=True)

        steps = [
            {
                "num": "1",
                "title": "Get Gemini Flash API Key (5 minutes)",
                "content": """
1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy it → paste as `GEMINI_API_KEY` in secrets.toml
5. Free tier: 15 requests/minute, 1 million tokens/day

**Cost: $0.00 forever on free tier**
                """,
            },
            {
                "num": "2",
                "title": "Set Up Supabase Database (10 minutes)",
                "content": """
1. Go to **https://supabase.com** → Sign up free
2. Create New Project (any name, e.g. "deal-finder")
3. Wait ~2 min for provisioning
4. Go to **Settings → API**
5. Copy **Project URL** → `SUPABASE_URL`
6. Copy **anon/public** key → `SUPABASE_ANON_KEY`
7. Go to **SQL Editor** → paste and run the SQL from `utils/database.py` (the `SETUP_SQL` variable)
   This creates the leads, outreach, and agent_runs tables.

**Cost: $0.00 on free tier (500MB, unlimited API calls)**
                """,
            },
            {
                "num": "3",
                "title": "Set Up Gmail API (15 minutes)",
                "content": """
1. Go to **https://console.cloud.google.com**
2. Create a new project (e.g. "deal-finder")
3. Enable **Gmail API**: APIs & Services → Library → search "Gmail API" → Enable
4. Create credentials: APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
5. Application type: **Desktop app**
6. Download the JSON file
7. Run this one-time script locally to get your refresh token:

```bash
pip install google-auth-oauthlib google-api-python-client
python gmail_auth.py
```

8. Paste the output JSON into `GMAIL_CREDENTIALS_JSON` in secrets.toml

**Cost: $0.00 — Gmail API has no usage fees**
                """,
            },
            {
                "num": "4",
                "title": "Deploy to Streamlit Community Cloud (5 minutes)",
                "content": """
1. Push your code to a **private** GitHub repo
2. Go to **https://share.streamlit.io**
3. Sign in with GitHub → Deploy an app
4. Select your repo and `app.py` as the main file
5. Go to **Settings → Secrets** → paste your entire secrets.toml content
6. Click Deploy

**Cost: $0.00 — Streamlit Community Cloud is free**

Your app will be live at: `https://yourname-deal-finder.streamlit.app`
                """,
            },
            {
                "num": "5",
                "title": "Run the Supabase SQL Setup",
                "content": """
After creating your Supabase project, run this SQL in the SQL Editor to create all tables:

```sql
-- Copy the SETUP_SQL from utils/database.py and run it
-- in Supabase SQL Editor: https://supabase.com/dashboard/project/YOUR_ID/sql/new
```

This creates:
- `leads` table (real estate + business leads)
- `outreach` table (all emails sent with timestamps)
- `agent_runs` table (execution logs)
                """,
            },
        ]

        for step in steps:
            with st.expander(f"Step {step['num']}: {step['title']}", expanded=False):
                st.markdown(step["content"])

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title" style="font-size:1.1rem;">Gmail Auth Script</div>', unsafe_allow_html=True)
        st.markdown("Save this as `gmail_auth.py` and run it locally once to get your credentials JSON:")

        st.code("""
# gmail_auth.py — run once locally to generate credentials
# pip install google-auth-oauthlib google-api-python-client

import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.oauth2.credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Path to the client_secret JSON you downloaded from Google Cloud Console
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0)

# Print credentials JSON to paste into secrets.toml
output = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
}
print("\\nPaste this as GMAIL_CREDENTIALS_JSON in secrets.toml:")
print(json.dumps(output))
        """, language="python")

    with tab3:
        st.markdown('<div class="section-title" style="font-size:1.1rem;">Test Your Connections</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🤖 Test Gemini AI", use_container_width=True):
                from utils.gemini import ask
                result = ask("Respond with exactly: GEMINI_OK")
                if result and "GEMINI_OK" in result:
                    st.success("✅ Gemini connected!")
                elif result:
                    st.success(f"✅ Gemini connected: {result[:50]}")
                else:
                    st.error("❌ Gemini failed — check GEMINI_API_KEY in secrets")

        with col2:
            if st.button("🗄️ Test Supabase", use_container_width=True):
                from utils.database import get_client
                client = get_client()
                if client:
                    try:
                        client.table("leads").select("id").limit(1).execute()
                        st.success("✅ Supabase connected!")
                    except Exception as e:
                        st.warning(f"⚠️ Connected but table missing. Run the SQL setup. ({e})")
                else:
                    st.error("❌ Supabase failed — check SUPABASE_URL and SUPABASE_ANON_KEY")

        with col3:
            if st.button("📧 Test Gmail", use_container_width=True):
                from utils.gmail_sender import test_connection
                if test_connection():
                    st.success("✅ Gmail connected!")
                else:
                    st.info("ℹ️ Gmail not configured — emails will simulate (log but not send)")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        <strong>Running without Gmail?</strong> That's fine for now — the app will log all outreach
        in "simulated" mode. You can see every email that <em>would have been sent</em> in the
        Outreach Log. Set up Gmail when ready to go live.
        </div>
        """, unsafe_allow_html=True)
