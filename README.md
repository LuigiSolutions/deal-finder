# Northern Michigan Deal Finder
**AI-powered acquisition lead discovery & outreach — Real Estate · Businesses**

Zero cost. Deployed on Streamlit Community Cloud.

---

## What It Does

Two AI agents that run on demand (or on a schedule):

**Real Estate Agent**
- Searches Craigslist FSBO + web for motivated sellers in Northern Michigan
- Targets seller financing, subject-to, lease-option, and DSCR income property deals
- Scores each lead 1-10 based on motivated seller signals
- Writes personalized outreach emails via Gemini Flash
- Sends via Gmail API and logs everything to Supabase

**Business Agent**
- Searches BizBuySell + web for owner-operated Northern Michigan businesses
- Targets SBA 7(a) + seller carry acquisition opportunities
- Identifies exit signals (owner age, listing tenure, no succession plan)
- Same email outreach and logging pipeline

**Outreach Log**
- Every email sent: owner name, email, business/property name, subject, full body, date/time stamp
- Filter by type, status, export to CSV
- Mark replies manually

---

## Total Cost: $0

| Service | Free Tier | Limit |
|---|---|---|
| Gemini Flash (AI) | Free | 1M tokens/day, 15 req/min |
| Supabase (Database) | Free | 500MB, unlimited API calls |
| Gmail API (Email) | Free | No usage fees |
| Streamlit Cloud (Hosting) | Free | Unlimited public apps |

---

## Setup (30 minutes total)

### 1. Gemini API Key (5 min)
1. Go to https://aistudio.google.com/app/apikey
2. Create API Key
3. Paste as `GEMINI_API_KEY` in secrets

### 2. Supabase (10 min)
1. Create free project at https://supabase.com
2. Copy Project URL and anon key from Settings → API
3. Run the SQL from `utils/database.py` (`SETUP_SQL` variable) in SQL Editor

### 3. Gmail API (15 min)
1. Go to https://console.cloud.google.com → New Project
2. Enable Gmail API (APIs & Services → Library)
3. Create OAuth 2.0 credentials (Desktop app) → download JSON
4. Run locally: `python gmail_auth.py`
5. Paste output into `GMAIL_CREDENTIALS_JSON` in secrets

### 4. Deploy to Streamlit Cloud (5 min)
1. Push to private GitHub repo (never commit secrets.toml)
2. Go to https://share.streamlit.io → Deploy
3. Add secrets in App Settings → Secrets

---

## Local Development

```bash
# Clone / copy project
cd deal-finder

# Install dependencies
pip install -r requirements.txt

# Create secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your keys

# Run
streamlit run app.py
```

---

## No Money Down Acquisition Strategies

**Real Estate**
- **Seller Financing** — Seller acts as the bank. Negotiate terms directly.
- **Subject-To** — Take over existing mortgage payments. Deed transfers, loan stays in seller's name.
- **Lease-Option** — Lease with right to buy. Controls asset without ownership.
- **DSCR Loans** — Bank lends based on property income, not your income.

**Business Acquisitions**
- **SBA 7(a)** — Bank finances 90% of purchase. Business cashflow services the debt.
- **Seller Carry** — Seller finances 10% as a note = near-zero out of pocket.
- **SBA + Seller Carry** — Combined = $0 down in many cases.

---

## Architecture

```
app.py                    — Streamlit entry point + navigation
pages/
  dashboard.py            — Stats overview + recent activity
  real_estate.py          — RE agent + lead management
  business.py             — Business agent + lead management
  outreach_log.py         — Full timestamped outreach history
  settings.py             — API key setup + connection tests
utils/
  database.py             — Supabase client + all DB operations
  gemini.py               — Gemini Flash AI prompts + parsing
  gmail_sender.py         — Gmail API email sender
  scraper.py              — Free web scrapers (no API cost)
.streamlit/
  config.toml             — Dark theme with navy/gold colors
  secrets.toml            — Your API keys (never commit this)
```
