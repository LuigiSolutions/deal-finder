import streamlit as st


def render():
    st.markdown('<div class="section-title">⚙️ Settings & Setup Guide</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🔑 API Keys", "📋 Setup Guide", "🧪 Test Connections", "📤 Test Outreach"])

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

# ── FREE: OpenRouter AI ───────────────────────────────────
# Get free key at: https://openrouter.ai/ (no credit card)
# Find free models at: https://openrouter.ai/models?q=free
OPENROUTER_API_KEY = "sk-or-..."
OPENROUTER_MODEL = "deepseek/deepseek-r1:free"

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
                "title": "Get OpenRouter API Key (2 minutes)",
                "content": """
1. Go to **https://openrouter.ai/** → sign up free (no credit card)
2. Click **Keys** in the left sidebar → **Create Key**
3. Copy it → paste as `OPENROUTER_API_KEY` in secrets
4. Go to **https://openrouter.ai/models?q=free** to see available free models
5. Pick one and paste the model ID as `OPENROUTER_MODEL` in secrets
   - Example: `deepseek/deepseek-r1:free`

**Cost: $0.00 — free models require no billing setup**
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
            if st.button("🤖 Test AI", use_container_width=True):
                from utils.gemini import ask
                result = ask("Respond with exactly: OK")
                if result and "OK" in result:
                    st.success(f"✅ AI connected!")
                elif result:
                    st.success(f"✅ AI connected: {result[:60]}")
                else:
                    st.error("❌ AI failed — check OPENROUTER_API_KEY and OPENROUTER_MODEL in secrets")

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
                ok, detail = test_connection()
                if ok:
                    st.success(f"✅ Gmail connected: {detail}")
                else:
                    st.warning(f"⚠️ Gmail: {detail}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        <strong>Running without Gmail?</strong> That's fine for now — the app will log all outreach
        in "simulated" mode. You can see every email that <em>would have been sent</em> in the
        Outreach Log. Set up Gmail when ready to go live.
        </div>
        """, unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="section-title" style="font-size:1.1rem;">Test Outreach — Send to Yourself</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        Sends one real estate email and one business email to <strong>your own address</strong>
        using demo leads and live Gemini AI. Lets you review the exact tone and content before
        going live. Requires Gemini and Gmail to be configured.
        </div>
        """, unsafe_allow_html=True)

        from utils import scraper as _scraper, gemini as _gemini, gmail_sender as _gmail

        to_addr = st.secrets.get("GMAIL_FROM_ADDRESS", "luigisolutions7@gmail.com")
        sender_name = st.secrets.get("YOUR_NAME", "Kalob")

        st.markdown(f"Test emails will be sent to **{to_addr}**")
        st.markdown("<br>", unsafe_allow_html=True)

        col_re, col_biz = st.columns(2)

        # ── Real Estate test ──────────────────────────────────────────────────
        with col_re:
            st.markdown("**🏠 Real Estate Lead**")
            re_leads = _scraper.get_demo_re_leads()
            re_names = [f"{l['name']} ({l['city']})" for l in re_leads]
            re_idx = st.selectbox("Pick a demo lead", range(len(re_names)),
                                  format_func=lambda i: re_names[i], key="test_re_lead")
            re_lead = re_leads[re_idx]

            with st.expander("Lead details", expanded=False):
                st.json({k: v for k, v in re_lead.items() if k not in ("type",)})

            if st.button("Generate & Send RE Test Email", key="test_re_btn", use_container_width=True):
                with st.spinner("Writing email with Gemini..."):
                    email_data = _gemini.write_re_email(re_lead, sender_name)

                if not email_data:
                    st.error("AI failed to generate the email — check OPENROUTER_API_KEY and OPENROUTER_MODEL in secrets.")
                else:
                    st.markdown(f"**Subject:** {email_data['subject']}")
                    st.text_area("Body preview", email_data["body"], height=200, key="test_re_body")

                    subject = f"[TEST → {re_lead.get('owner_name','Owner')}] {email_data['subject']}"
                    result = _gmail.send_email(
                        to_email=to_addr,
                        subject=subject,
                        body=email_data["body"],
                        from_name=sender_name,
                    )
                    if result["success"] and not result.get("simulated"):
                        st.success(f"✅ Sent to {to_addr}")
                    elif result.get("simulated"):
                        st.info("📧 Simulated (Gmail not configured) — see body preview above")
                    else:
                        st.error(f"Send failed: {result['error']}")

        # ── Business test ─────────────────────────────────────────────────────
        with col_biz:
            st.markdown("**🏢 Business Lead**")
            biz_leads = _scraper.get_demo_biz_leads()
            biz_names = [f"{l['name']} ({l['city']})" for l in biz_leads]
            biz_idx = st.selectbox("Pick a demo lead", range(len(biz_names)),
                                   format_func=lambda i: biz_names[i], key="test_biz_lead")
            biz_lead = biz_leads[biz_idx]

            with st.expander("Lead details", expanded=False):
                st.json({k: v for k, v in biz_lead.items() if k not in ("type",)})

            if st.button("Generate & Send Biz Test Email", key="test_biz_btn", use_container_width=True):
                with st.spinner("Writing email with Gemini..."):
                    email_data = _gemini.write_biz_email(biz_lead, sender_name)

                if not email_data:
                    st.error("AI failed to generate the email — check OPENROUTER_API_KEY and OPENROUTER_MODEL in secrets.")
                else:
                    st.markdown(f"**Subject:** {email_data['subject']}")
                    st.text_area("Body preview", email_data["body"], height=200, key="test_biz_body")

                    subject = f"[TEST → {biz_lead.get('owner_name','Owner')}] {email_data['subject']}"
                    result = _gmail.send_email(
                        to_email=to_addr,
                        subject=subject,
                        body=email_data["body"],
                        from_name=sender_name,
                    )
                    if result["success"] and not result.get("simulated"):
                        st.success(f"✅ Sent to {to_addr}")
                    elif result.get("simulated"):
                        st.info("📧 Simulated (Gmail not configured) — see body preview above")
                    else:
                        st.error(f"Send failed: {result['error']}")
