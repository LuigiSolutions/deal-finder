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
- Sends via Gmail API and logs everything to Supabase + Obsidian vault

**Business Agent**
- Searches BizBuySell + web for owner-operated Northern Michigan businesses
- Targets SBA 7(a) + seller carry acquisitions (near-zero down)
- Same scoring, ordering, email, and vault pipeline

**Outreach Log**
- Every email sent: owner name, email, subject, full body, date/time stamp
- Filter by type, status, export to CSV

**Settings → Test Outreach tab**
- Generate real AI emails from demo leads and send to yourself before going live
- Not logged to vault or database — preview only

**🕸️ Knowledge Graph page (in-app)**
- Interactive network graph built with pyvis, rendered inside Streamlit
- Toggle between demo leads and real leads from the database
- Lead nodes colored by score (green/gold/red), city and deal type hub nodes
- Draggable, zoomable, hover tooltips on every node

**Obsidian Knowledge Graph (local)**
- Every lead also auto-written as a markdown note to `vault/`
- Demo leads → `vault/leads/demo/`, real leads → `vault/leads/`
- Open `vault/` folder in Obsidian for the desktop graph view

---

## Total Cost: $0

| Service | Free Tier | Notes |
|---|---|---|
| OpenRouter (AI) | Free | No credit card. Model set via `OPENROUTER_MODEL` secret |
| Supabase (Database) | Free | 500MB, unlimited API calls |
| Gmail API (Email) | Free | No usage fees |
| Streamlit Cloud (Hosting) | Free | Unlimited public apps |
| Obsidian | Free | Local app; open vault/ folder as a vault |

---

## Setup

### 1. OpenRouter API Key (2 min)
1. Go to https://openrouter.ai/ → sign up free (no credit card)
2. Click **Keys** → **Create Key**
3. Go to https://openrouter.ai/models?q=free and pick a free model — copy its exact ID
4. Add to Streamlit secrets:
   ```
   OPENROUTER_API_KEY = "sk-or-..."
   OPENROUTER_MODEL = "openai/gpt-oss-120b:free"
   ```
   If a model gets removed, update `OPENROUTER_MODEL` in Streamlit secrets — no code push needed.

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

### 5. Obsidian Knowledge Graph (1 min)
1. Download Obsidian at https://obsidian.md (free)
2. Open Obsidian → **Open folder as vault**
3. Navigate to the `vault/` folder inside this project
4. Click **Open** — the graph is ready with 6 demo leads pre-seeded

---

## Mobile Support

The app is optimized for both desktop and mobile. CSS media queries activate on small screens without touching desktop styles:

- Header and metric fonts scale down for small screens
- Buttons are minimum 44px tall for comfortable touch targets
- Text inputs use `font-size: 16px` to prevent iOS auto-zoom on focus
- Sidebar nav tap targets are larger on mobile
- Hover effects disabled on touch (no accidental lifts)
- Knowledge Graph shows a landscape orientation tip on mobile

Desktop layout and all styling is fully preserved — mobile CSS only activates via `@media (max-width: 768px)`.

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

## Email Writing Rules

Every outreach email enforces these rules via prompt injection:
- No em dashes (—)
- No exclamation points
- No filler openers ("I hope this finds you well", "I came across", "I wanted to reach out")
- No corporate buzzwords
- Short sentences, plain English
- First name sign-off only
- Exactly one low-pressure question at the end

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
  vault.py                — Obsidian vault writer (auto-called on every lead save)
vault/
  Home.md                 — Project overview note
  leads/                  — Real lead notes (live scraping)
  leads/demo/             — Demo lead notes (demo mode)
  _hubs/                  — City, deal type, owner hub notes (graph clusters)
.streamlit/
  config.toml             — Dark theme (navy/gold)
  secrets.toml            — Your API keys (never commit this)
```
