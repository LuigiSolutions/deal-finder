# Northern Michigan Deal Finder
**AI-powered acquisition lead discovery & outreach — Real Estate · Businesses**

Zero cost. Deployed at **deal-finder7.streamlit.app** on Streamlit Community Cloud.

---

## What It Does

Two AI agents that run on demand:

**Real Estate Agent**
- Searches Craigslist FSBO + web for motivated sellers in Northern Michigan
- Scores each lead 1-10 using a 4-factor rubric (timeline, bank involvement, down payment, motivation signals)
- Highest-scoring leads contacted first
- Writes personalized outreach emails via OpenRouter AI
- Sends via Gmail API and logs everything to Supabase

**Business Agent**
- Searches BizBuySell + web for owner-operated Northern Michigan businesses
- Targets SBA 7(a) + seller carry acquisitions (near-zero down)
- Same scoring, ordering, and email pipeline

**Outreach Log**
- Every email sent: owner name, email, subject, full body, date/time stamp
- Filter by type, status, export to CSV

**Settings → Test Outreach tab**
- Generate real AI emails from demo leads and send to yourself before going live

---

## Total Cost: $0

| Service | Free Tier | Notes |
|---|---|---|
| OpenRouter (AI) | Free | No credit card. Model set via `OPENROUTER_MODEL` secret |
| Supabase (Database) | Free | 500MB, unlimited API calls |
| Gmail API (Email) | Free | No usage fees |
| Streamlit Cloud (Hosting) | Free | Unlimited public apps |

---

## Setup

### 1. OpenRouter API Key (2 min)
1. Go to https://openrouter.ai/ → sign up free (no credit card)
2. Click **Keys** → **Create Key**
3. Go to https://openrouter.ai/models?q=free and pick a free model — copy its ID
4. Add to Streamlit secrets:
   ```
   OPENROUTER_API_KEY = "sk-or-..."
   OPENROUTER_MODEL = "openai/gpt-oss-120b:free"
   ```

### 2. Supabase (10 min)
1. Create free project at https://supabase.com
2. Copy Project URL and anon key from Settings → API
3. Run the SQL from `utils/database.py` (`SETUP_SQL` variable) in SQL Editor
4. Add to Streamlit secrets:
   ```
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_ANON_KEY = "eyJ..."
   ```

### 3. Gmail API (15 min)
1. Go to https://console.cloud.google.com → New Project
2. Enable Gmail API (APIs & Services → Library)
3. Create OAuth 2.0 credentials (Desktop app) → download JSON as `client_secret.json`
4. Run locally: `python gmail_auth.py` (opens browser for Google sign-in)
5. Copy the printed JSON and paste as `GMAIL_CREDENTIALS_JSON` in Streamlit secrets
   - The access token auto-refreshes on every call — no manual renewal needed

### 4. Deploy to Streamlit Cloud (5 min)
1. Push to a GitHub repo (never commit `.streamlit/secrets.toml`)
2. Go to https://share.streamlit.io → Deploy → select `app.py`
3. Add all secrets in App Settings → Secrets → Save

---

## Local Development

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# fill in your keys
streamlit run app.py
```

---

## Lead Scoring Rubric (1-10)

Higher score = better deal for a buyer who wants little to no money down and no bank.

| Factor | Best (HIGH) | Worst (LOW) |
|---|---|---|
| Seller timeline | Immediate / urgent | Years away / no rush |
| Bank involvement | No bank (seller finance, subject-to) | Full conventional loan required |
| Down payment | Near zero | Large cash requirement |
| Motivation signals | Estate, divorce, retirement, long DOM | Fresh listing, no signals |

A **10** = sell immediately, $0 down, no bank involved.  
A **1** = selling someday, large down payment, bank only.

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
  settings.py             — API key setup + connection tests + test outreach
utils/
  database.py             — Supabase client + all DB operations (leads sorted score DESC)
  gemini.py               — OpenRouter AI: prompts, EMAIL_RULES, SCORING_RUBRIC
  gmail_sender.py         — Gmail API email sender (auto token refresh)
  scraper.py              — Free web scrapers + demo lead data
.streamlit/
  config.toml             — Dark theme (navy/gold)
  secrets.toml            — Your API keys (never commit this)
```
