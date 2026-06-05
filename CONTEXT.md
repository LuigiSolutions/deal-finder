# Northern Michigan Deal Finder — Project Context

## What This Is

A Streamlit app that runs two AI-powered acquisition lead agents:
- **Real Estate Agent**: Finds motivated sellers in Northern Michigan (FSBO, long DOM, estate sales). Targets seller financing, subject-to, lease-option, and DSCR deals.
- **Business Agent**: Finds owner-operated businesses on BizBuySell + web. Targets SBA 7(a) + seller carry acquisitions (near-zero down).

Both agents scrape, score leads with Gemini AI, write personalized outreach emails, send via Gmail API, and log everything to Supabase.

**Deployed at**: deal-finder7.streamlit.app  
**Owner/sender persona**: Kalob Hagen (`luigisolutions7@gmail.com`)

---

## Tech Stack (all free tier)

| Layer | Service | Notes |
|---|---|---|
| Hosting | Streamlit Community Cloud | app.py is entry point |
| AI | Gemini 1.5 Flash | Via `google-generativeai`; 1M tokens/day free |
| Database | Supabase (Postgres) | 3 tables: leads, outreach, agent_runs |
| Email | Gmail API (OAuth2) | OAuth user credentials, not service account |
| Scraping | `requests` + Craigslist/BizBuySell | No paid APIs |

---

## File Structure

```
app.py                    — Streamlit entry point, CSS, navigation router
pages/
  dashboard.py            — Stats overview and recent activity
  real_estate.py          — RE agent + lead list
  business.py             — Business agent + lead list
  outreach_log.py         — Full email log with filter/export
  settings.py             — API key setup, step-by-step guide, connection tests
utils/
  database.py             — Supabase client; leads/outreach/agent_runs CRUD
  gemini.py               — Gemini prompts: lead extraction, email writing, scoring
  gmail_sender.py         — Gmail API OAuth sender; get_gmail_service(), send_email(), test_connection()
  scraper.py              — Web scrapers (Craigslist, BizBuySell)
.streamlit/
  config.toml             — Dark theme (navy #0a1628, gold #B8860B)
  secrets.toml            — Local secrets (gitignored)
  secrets.toml.example    — Template for onboarding
gmail_auth.py             — One-time local script to generate OAuth credentials JSON
client_secret.json        — OAuth client secret from Google Cloud Console (gitignored)
requirements.txt
```

---

## Secrets (Streamlit Cloud Dashboard → App Settings → Secrets)

```toml
YOUR_NAME = "Kalob Hagen"
GEMINI_API_KEY = "AIza..."
SUPABASE_URL = "https://zpeenadlelnlqfmmumod.supabase.co"
SUPABASE_ANON_KEY = "..."
GMAIL_CREDENTIALS_JSON = '{"token":"...","refresh_token":"...","client_id":"...","client_secret":"..."}'
GMAIL_FROM_ADDRESS = "luigisolutions7@gmail.com"
```

**Important**: `GMAIL_CREDENTIALS_JSON` must be a single-line JSON string or a triple-quoted TOML string containing the OAuth user credentials (not the `client_secret.json` from Google Cloud Console). Generate it by running `gmail_auth.py` locally once.

---

## Gmail OAuth Flow

1. Download `client_secret.json` from Google Cloud Console (OAuth 2.0 Desktop App credentials)
2. Run `python gmail_auth.py` locally — it opens a browser for Google sign-in
3. Copy the printed JSON and paste as `GMAIL_CREDENTIALS_JSON` in Streamlit secrets

**Why the stored token doesn't expire**: The credentials include a `refresh_token` (long-lived). `get_gmail_service()` always calls `creds.refresh(GoogleRequest())` before building the service, so the short-lived access token is renewed automatically on every call.

---

## Database Schema

```sql
leads       — one row per discovered property or business
outreach    — every email sent; references leads.id
agent_runs  — log of each agent execution with start/end/status
```

Run `SETUP_SQL` from `utils/database.py` once in Supabase SQL Editor to create all tables. Falls back to `st.session_state` in-memory storage when Supabase is not configured.

---

## Brand / UI

- Colors: Navy `#0a1628` background, Gold `#B8860B`/`#FFD700` accents
- Fonts: Bebas Neue (headers), Inter (body)
- All custom CSS injected via `st.markdown()` in `app.py`

---

## Known Working State (2026-06-05)

- Gemini AI: working
- Supabase: working (project `zpeenadlelnlqfmmumod`)
- Gmail: credentials configured in cloud secrets; token refresh added in latest fix
- Streamlit Cloud: deployed and accessible
