# Northern Michigan Deal Finder — Project Context

## What This Is

A Streamlit app that runs two AI-powered acquisition lead agents:
- **Real Estate Agent**: Finds motivated sellers in Northern Michigan (FSBO, long DOM, estate sales). Targets seller financing, subject-to, lease-option, and DSCR deals.
- **Business Agent**: Finds owner-operated businesses on BizBuySell + web. Targets SBA 7(a) + seller carry acquisitions (near-zero down).

Both agents scrape, score leads with AI, write personalized outreach emails, send via Gmail API, log everything to Supabase, and write every lead as a markdown note to an Obsidian vault. Leads are always sorted and contacted highest-score-first.

**Deployed at**: deal-finder7.streamlit.app  
**Owner/sender persona**: Kalob Hagen (`luigisolutions7@gmail.com`)

---

## Tech Stack (all free tier)

| Layer | Service | Notes |
|---|---|---|
| Hosting | Streamlit Community Cloud | app.py is entry point |
| AI | OpenRouter (free models) | Via `requests`; model set in secrets as `OPENROUTER_MODEL` |
| Database | Supabase (Postgres) | 3 tables: leads, outreach, agent_runs |
| Email | Gmail API (OAuth2) | OAuth user credentials, not service account |
| Scraping | `requests` + Craigslist/BizBuySell | No paid APIs |
| Knowledge Graph | Obsidian vault | Markdown files auto-written per lead; open `vault/` folder in Obsidian |

---

## File Structure

```
app.py                    — Streamlit entry point, CSS, navigation router
pages/
  dashboard.py            — Stats overview and recent activity
  real_estate.py          — RE agent + lead list
  business.py             — Business agent + lead list
  outreach_log.py         — Full email log with filter/export
  settings.py             — API key setup, step-by-step guide, connection tests, test outreach tab
utils/
  database.py             — Supabase client; leads/outreach/agent_runs CRUD; leads ordered score DESC
  gemini.py               — OpenRouter AI: lead extraction, email writing, scoring (EMAIL_RULES + SCORING_RUBRIC)
  gmail_sender.py         — Gmail API OAuth sender; always refreshes token before use
  scraper.py              — Web scrapers (Craigslist, BizBuySell) + demo lead data
  vault.py                — Obsidian vault writer; write_lead(), log_outreach_to_vault()
vault/
  Home.md                 — Project overview note with scoring rubric and city links
  leads/                  — Real lead notes (written when agents run in live mode)
  leads/demo/             — Demo lead notes (written when agents run in demo mode)
  _hubs/                  — Auto-created city, deal type, and owner hub notes for graph clustering
.streamlit/
  config.toml             — Dark theme (navy #0a1628, gold #B8860B)
  secrets.toml            — Local secrets (gitignored)
  secrets.toml.example    — Template for onboarding
gmail_auth.py             — One-time local script to generate OAuth credentials JSON
client_secret.json        — OAuth client secret from Google Cloud Console (gitignored)
requirements.txt
CONTEXT.md                — This file
```

---

## Secrets (Streamlit Cloud Dashboard → App Settings → Secrets)

```toml
YOUR_NAME = "Kalob Hagen"

# OpenRouter — free, no credit card. Get key at https://openrouter.ai/
# Find current free models at https://openrouter.ai/models?q=free
OPENROUTER_API_KEY = "sk-or-..."
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"  # update if model is removed

SUPABASE_URL = "https://zpeenadlelnlqfmmumod.supabase.co"
SUPABASE_ANON_KEY = "..."

GMAIL_CREDENTIALS_JSON = '{"token":"...","refresh_token":"...","client_id":"...","client_secret":"..."}'
GMAIL_FROM_ADDRESS = "luigisolutions7@gmail.com"
```

**OPENROUTER_MODEL**: Can be swapped in Streamlit Cloud secrets without a code push. If a model returns 404, go to openrouter.ai/models?q=free and pick a new one.

**GMAIL_CREDENTIALS_JSON**: Must be a single-line JSON string or triple-quoted TOML string containing OAuth user credentials (not `client_secret.json`). Generate by running `gmail_auth.py` locally once.

---

## AI Layer — utils/gemini.py

Despite the filename, this module now uses OpenRouter (not Gemini). All public function signatures are unchanged.

**Key constants:**

`EMAIL_RULES` — injected into every outreach email prompt:
- No em dashes (—)
- No exclamation points
- No filler openers ("I hope this finds you well", "I came across", "I wanted to reach out")
- No corporate buzzwords
- Short sentences, plain English
- First name sign-off only
- Exactly one low-pressure question at the end

`SCORING_RUBRIC` — injected into all scoring and lead extraction prompts. Scores 1-10 on four factors (bank involvement and down payment weighted most heavily):
1. Seller timeline urgency
2. Bank involvement (seller finance = best, conventional = worst)
3. Down payment / entry cost (near zero = best)
4. Motivated seller signals

A 10 = seller wants to sell immediately, $0 down, no bank. A 1 = selling in years, large down payment, bank required.

**Public functions**: `ask()`, `ask_json()`, `generate_re_leads()`, `write_re_email()`, `generate_biz_leads()`, `write_biz_email()`, `score_deal()`

---

## Obsidian Vault — vault/

Open the `vault/` folder in Obsidian ("Open folder as vault") to get the knowledge graph.

**How it works:**
- Every `upsert_lead()` call writes a markdown note automatically
- Demo leads (agent run with "Use demo data" ON) → `vault/leads/demo/`
- Real leads (live scraping) → `vault/leads/`
- Test Outreach tab emails → NOT logged (correct — they're just previews)
- Every `log_outreach()` call appends the email to the lead's note under "Outreach Log"
- Hub notes for each city, deal type, and owner are auto-created in `_hubs/` — these become the graph cluster nodes

**Vault structure in the graph:**
- City hubs (Traverse City, Petoskey, etc.) cluster all leads from that area
- Deal type hubs (seller_finance, sba_plus_seller_carry, etc.) cluster by strategy
- Owner hubs link deals connected to the same person

**Adding your own notes:** Each lead note has a "My Notes" section at the bottom — add follow-up reminders, conversation notes, etc. Agent re-runs update the auto-generated sections but preserve your manual notes section.

---

## Gmail OAuth Flow

1. Download `client_secret.json` from Google Cloud Console (OAuth 2.0 Desktop App credentials)
2. Run `python gmail_auth.py` locally — it opens a browser for Google sign-in
3. Copy the printed JSON and paste as `GMAIL_CREDENTIALS_JSON` in Streamlit secrets

**Why the stored token never expires**: `get_gmail_service()` always calls `creds.refresh(GoogleRequest())` before building the service, so the short-lived access token is renewed on every call using the long-lived `refresh_token`.

**Scope**: Only `gmail.send` is authorized. `test_connection()` does NOT call `getProfile` (requires `gmail.readonly`) — it validates by checking that the service builds and the token refreshes successfully.

---

## Lead Scoring & Outreach Order

- All leads stored with a score 1-10
- `get_leads()` always returns leads ordered `score DESC`
- Agent qualifying lists sorted `score DESC` before emailing
- Agents contact the highest-scoring leads first and stop at the minimum score threshold

---

## Database Schema

```sql
leads       — one row per discovered property or business; ordered by score DESC
outreach    — every email sent; references leads.id
agent_runs  — log of each agent execution with start/end/status
```

Run `SETUP_SQL` from `utils/database.py` once in Supabase SQL Editor. Falls back to `st.session_state` in-memory storage when Supabase is not configured.

---

## Settings Page — 4 Tabs

1. **API Keys** — secrets template with correct OpenRouter format
2. **Setup Guide** — step-by-step instructions for all services
3. **Test Connections** — test AI, Supabase, Gmail individually
4. **Test Outreach** — generate real AI emails from demo leads and send to yourself for review; emails go to GMAIL_FROM_ADDRESS with [TEST] prefix; NOT logged to vault or database

---

## Brand / UI

- Colors: Navy `#0a1628` background, Gold `#B8860B`/`#FFD700` accents
- Fonts: Bebas Neue (headers), Inter (body)
- All custom CSS injected via `st.markdown()` in `app.py`

**Mobile optimization** (added via CSS media queries — desktop styles untouched):
- `≤768px`: smaller header (2rem), tighter metric cards, buttons min 44px height for touch targets, `font-size: 16px` on inputs to prevent iOS auto-zoom, bigger sidebar tap targets, no hover lift on buttons
- `≤480px`: extra-small phone adjustments (header 1.55rem, smaller metrics/section titles)
- Knowledge Graph page shows a landscape tip on mobile screens
- Streamlit handles sidebar collapse and column stacking natively on mobile

---

## Knowledge Graph Page — pages/graph.py

Interactive pyvis network graph rendered inside Streamlit. Accessible via **🕸️ Knowledge Graph** in the left sidebar.

- Toggle at top of page: **off = demo leads**, **on = real leads from database**
- Lead nodes colored by score: green (8-10), gold (5-7), red (1-4); sized by score
- City hub nodes (blue squares), deal type hub nodes (gold diamonds)
- Owner hubs only shown when the same owner appears on multiple leads
- Draggable, zoomable, hover tooltips on every node
- Stats summary below graph: total leads, RE count, biz count, avg score, top lead

---

## Known Working State (2026-06-05)

- OpenRouter AI: working with `openai/gpt-oss-120b:free`
- Gmail: working; token auto-refreshes on every send
- Supabase: working (project `zpeenadlelnlqfmmumod`)
- Streamlit Cloud: deployed at deal-finder7.streamlit.app
- Test Outreach tab: confirmed sending real AI-generated emails to luigisolutions7@gmail.com
- Obsidian vault: seeded with 6 demo leads; open vault/ in Obsidian to view graph
- Knowledge Graph page: working; demo/real toggle confirmed
