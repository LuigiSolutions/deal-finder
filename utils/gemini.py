"""
AI text generation via OpenRouter — free tier
Free models require no credit card.
Get your free key at: https://openrouter.ai/
"""

import streamlit as st
import json
import time
import re
import requests
from typing import Optional

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "mistralai/mistral-7b-instruct:free"

# ── EMAIL WRITING RULES ───────────────────────────────────────────────────────
# Injected into every outreach email prompt.

EMAIL_RULES = """
STRICT EMAIL WRITING RULES — follow every one:
- NO em dashes (—). Use a comma, period, or new sentence instead.
- NO exclamation points anywhere in the email.
- NO filler openers: never write "I hope this finds you well", "I wanted to reach out",
  "I came across your property/business", "My name is X and I", or any variation.
- NO corporate buzzwords: leverage, opportunity, synergy, utilize, facilitate, etc.
- NO passive voice constructions like "it is believed" or "it was noticed".
- Short sentences. Max 2-3 sentences per paragraph.
- Plain English. Write how a real local person texts a neighbor.
- No flattery about the property or business.
- Sign off with first name only — no title, no company name.
- Exactly one question at the very end. No more.
- The question must be low-pressure and easy to say no to.
"""

# ── DEAL SCORING RUBRIC ───────────────────────────────────────────────────────
# Used in all scoring prompts. Higher score = better deal for a buyer who
# wants little to no money down and no bank involvement.

SCORING_RUBRIC = """
DEAL SCORING RUBRIC (1-10 scale):

The ideal deal scores 10: seller wants to sell immediately, requires $0 down,
and no bank is involved (pure seller financing or subject-to).
The worst deal scores 1: seller wants to sell in many years, requires a massive
down payment, and only accepts full bank financing at full asking price.

Score based on these four factors:

1. SELLER TIMELINE (how urgently do they want to sell?)
   - Immediate / actively marketing / estate/divorce/foreclosure pressure = HIGH
   - Open to selling but no rush = MEDIUM
   - Someday, just exploring, no real motivation = LOW

2. BANK INVOLVEMENT (can this be done without a traditional bank loan?)
   - No bank needed: seller financing, subject-to, lease-option = HIGH
   - Minimal bank: DSCR loan or SBA + seller carry = MEDIUM
   - Full conventional bank financing required = LOW

3. DOWN PAYMENT / ENTRY COST (how much cash out of pocket?)
   - Near zero down: seller carry, creative structure = HIGH
   - Small down (SBA 10%, DSCR reserves) = MEDIUM
   - Large down payment required = LOW

4. MOTIVATED SELLER SIGNALS (evidence they'll negotiate)
   - Estate sale, divorce, health issues, retirement, no succession plan = HIGH
   - Long days on market, multiple price cuts, FSBO = MEDIUM
   - No signals, listing just went up at full price = LOW

Weight bank involvement and down payment most heavily.
A 10 requires HIGH on at least 3 of 4 factors.
A 5 is average: some motivation, some bank involvement, modest down.
A 1-2 is a deal that only works with full cash or conventional financing.
"""


def get_model():
    """Return API key if configured, else None."""
    return st.secrets.get("OPENROUTER_API_KEY", "") or None


def ask(prompt: str, system: str = "", retries: int = 3) -> Optional[str]:
    """Send a prompt to OpenRouter and return the text response."""
    api_key = get_model()
    if not api_key:
        return None

    model = st.secrets.get("OPENROUTER_MODEL", DEFAULT_MODEL)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(retries):
        try:
            resp = requests.post(
                OPENROUTER_BASE,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages},
                timeout=45,
            )
            if not resp.ok:
                err = f"{resp.status_code} {resp.reason}: {resp.text[:300]}"
                is_rate_limit = resp.status_code == 429
                if is_rate_limit and attempt < retries - 1:
                    time.sleep((attempt + 1) * 15)
                else:
                    st.warning(f"AI error: {err}")
                    return None
                continue
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            err = str(e)
            if attempt < retries - 1:
                time.sleep((attempt + 1) * 5)
            else:
                st.warning(f"AI error: {err}")
                return None
    return None


def ask_json(prompt: str, system: str = "") -> Optional[dict]:
    """Ask and parse JSON response."""
    json_system = (system or "") + "\n\nYou must respond with ONLY valid JSON. No markdown, no explanation, no code fences."
    raw = ask(prompt, json_system)
    if not raw:
        return None
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"[\[{].*[\]}]", clean, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


# ── REAL ESTATE PROMPTS ───────────────────────────────────────────────────────

RE_SYSTEM = """You are an expert real estate acquisition analyst specializing in Northern Michigan
(Traverse City, Petoskey, Charlevoix, Elk Rapids, Bellaire, Cadillac, Boyne City areas).

You help identify motivated sellers and off-market deal opportunities where creative financing
(seller financing, subject-to, lease-option) or DSCR loans could be used to acquire with
little to no money down.

When generating leads or emails, be specific, professional, and genuine — not spammy."""


def generate_re_leads(search_results: str, location: str) -> Optional[list]:
    """Extract and score real estate leads from raw search results."""
    prompt = f"""
Analyze these search results for Northern Michigan real estate and extract potential acquisition leads.

Location focus: {location}

Search results:
{search_results}

{SCORING_RUBRIC}

For each potential lead return a JSON object with:
{{
  "name": "property address or listing name",
  "address": "full address",
  "city": "city name",
  "owner_name": "owner name if available or null",
  "owner_email": "email if found or null",
  "owner_phone": "phone if found or null",
  "source_url": "URL if available",
  "score": <integer 1-10 using the rubric above>,
  "deal_type": "seller_finance | subject_to | lease_option | dscr | fsbo",
  "price_asking": "asking price or null",
  "motivated_signals": ["signal1", "signal2"],
  "notes": "brief analysis referencing which rubric factors drove the score"
}}

Return ONLY the JSON array sorted by score descending. If no viable leads, return [].
"""
    return ask_json(prompt, RE_SYSTEM)


def write_re_email(lead: dict, sender_name: str = "Kalob") -> Optional[dict]:
    """Write a personalized outreach email for a real estate lead."""
    prompt = f"""
Write a cold outreach email to a property owner about potentially purchasing their property
using flexible creative financing.

Property details:
- Address: {lead.get('address', 'the property')}
- City: {lead.get('city', 'Northern Michigan')}
- Owner name: {lead.get('owner_name', 'Property Owner')}
- Motivated signals: {lead.get('motivated_signals', [])}
- Deal type I'm considering: {lead.get('deal_type', 'seller financing')}
- My name: {sender_name}

{EMAIL_RULES}

Additional requirements:
- Max 150 words in the body
- Reference the specific property or area naturally
- Mention I can be flexible on structure (seller financing, etc.) in one sentence only

Return JSON:
{{
  "subject": "email subject line",
  "body": "full email body"
}}
"""
    return ask_json(prompt, RE_SYSTEM)


# ── BUSINESS ACQUISITION PROMPTS ──────────────────────────────────────────────

BIZ_SYSTEM = """You are a small business acquisition specialist focused on Northern Michigan.

You help identify owner-operated businesses that may be acquisition candidates using:
- SBA 7(a) loans (bank finances 90% based on business cashflow)
- Seller financing (seller carries a note)
- Combination: SBA 7(a) + seller carry = near-zero down

Target businesses: profitable, owner-operated, in recession-resistant sectors,
owners likely near retirement age or showing exit signals.
Areas: Traverse City, Petoskey, Charlevoix, Cadillac, Elk Rapids, Boyne City, MI."""


def generate_biz_leads(search_results: str, location: str) -> Optional[list]:
    """Extract business acquisition leads from search results."""
    prompt = f"""
Analyze these search results and identify small businesses in Northern Michigan
that could be acquisition targets.

Location: {location}

Search results:
{search_results}

{SCORING_RUBRIC}

For each lead return:
{{
  "name": "business name",
  "address": "address if available",
  "city": "city",
  "business_type": "e.g. restaurant, auto repair, landscaping",
  "owner_name": "owner name or null",
  "owner_email": "email or null",
  "owner_phone": "phone or null",
  "source_url": "listing URL if available",
  "score": <1-10 using the rubric above>,
  "asking_price": "price or null",
  "annual_revenue": "revenue if listed or null",
  "acquisition_method": "sba_7a | seller_finance | sba_plus_seller_carry",
  "exit_signals": ["signal1", "signal2"],
  "notes": "brief analysis referencing which rubric factors drove the score"
}}

Return ONLY a JSON array sorted by score descending. If nothing viable, return [].
"""
    return ask_json(prompt, BIZ_SYSTEM)


def write_biz_email(lead: dict, sender_name: str = "Kalob") -> Optional[dict]:
    """Write outreach email to a business owner about acquisition."""
    prompt = f"""
Write a cold outreach email to a small business owner in Northern Michigan
about whether they would ever consider selling their business.

Business details:
- Business: {lead.get('name')}
- Type: {lead.get('business_type', 'business')}
- City: {lead.get('city', 'Northern Michigan')}
- Owner: {lead.get('owner_name', 'Business Owner')}
- Acquisition method I'm considering: {lead.get('acquisition_method', 'SBA loan + seller carry')}
- My name: {sender_name}

{EMAIL_RULES}

Additional requirements:
- 120-160 words max
- Acknowledge they may not be looking to sell
- Mention financing flexibility in one sentence (SBA + seller carry options)
- Reference Northern Michigan or the local community naturally

Return JSON:
{{
  "subject": "subject line",
  "body": "email body"
}}
"""
    return ask_json(prompt, BIZ_SYSTEM)


def score_deal(lead: dict, lead_type: str) -> int:
    """Score a deal 1-10 using the standard rubric."""
    prompt = f"""
Score this {lead_type} acquisition opportunity from 1-10.

{SCORING_RUBRIC}

Lead data:
{json.dumps(lead, indent=2)}

Respond with ONLY a single integer 1-10. No explanation.
"""
    result = ask(prompt)
    if result:
        match = re.search(r"\b([1-9]|10)\b", result)
        if match:
            return int(match.group())
    return 5
