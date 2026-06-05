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
DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct:free"


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
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            err = str(e)
            is_rate_limit = "429" in err or "quota" in err.lower() or "rate" in err.lower()
            if is_rate_limit and attempt < retries - 1:
                time.sleep((attempt + 1) * 15)
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


# ── REAL ESTATE PROMPTS ────────────────────────────────────────────────────────

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

For each potential lead, assess:
1. Motivated seller signals (long DOM, price cuts, estate sale, divorce, vacancy, etc.)
2. Creative financing suitability (owner-occupied = more likely to do seller financing)
3. Income property potential (for DSCR qualification)

Return a JSON array where each object has:
{{
  "name": "property address or listing name",
  "address": "full address",
  "city": "city name",
  "owner_name": "owner name if available or null",
  "owner_email": "email if found or null",
  "owner_phone": "phone if found or null",
  "source_url": "URL if available",
  "score": <integer 1-10, 10 = most motivated/best deal>,
  "deal_type": "seller_finance | subject_to | lease_option | dscr | fsbo",
  "price_asking": "asking price or null",
  "motivated_signals": ["signal1", "signal2"],
  "notes": "brief analysis"
}}

Return ONLY the JSON array. If no viable leads found, return [].
"""
    return ask_json(prompt, RE_SYSTEM)


def write_re_email(lead: dict, sender_name: str = "Kalob") -> Optional[dict]:
    """Write a personalized, non-spammy outreach email for a real estate lead."""
    prompt = f"""
Write a short, genuine cold outreach email to a property owner about potentially purchasing their property
using flexible/creative financing.

Property details:
- Address: {lead.get('address', 'the property')}
- City: {lead.get('city', 'Northern Michigan')}
- Owner name: {lead.get('owner_name', 'Property Owner')}
- Deal signals: {lead.get('motivated_signals', [])}
- Deal type I'm considering: {lead.get('deal_type', 'seller financing')}
- My name: {sender_name}

Requirements:
- Max 150 words in the body
- Sound like a real human, NOT a form letter
- Reference the specific property/area
- Briefly mention I can be flexible on structure (seller financing, etc.)
- End with a low-pressure single question
- DO NOT sound desperate or like mass outreach
- DO NOT use phrases like "I came across your property" or "I hope this finds you well"

Return JSON:
{{
  "subject": "email subject line",
  "body": "full email body"
}}
"""
    return ask_json(prompt, RE_SYSTEM)


# ── BUSINESS ACQUISITION PROMPTS ───────────────────────────────────────────────

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

Look for:
- Businesses listed for sale on BizBuySell or similar
- Owner-operated businesses in succession-risk industries (restaurants, retail, service, auto, medical, dental, etc.)
- Businesses where owner age/tenure suggests exit planning
- Recession-resistant cash flow businesses

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
  "score": <1-10 acquisition attractiveness>,
  "asking_price": "price or null",
  "annual_revenue": "revenue if listed or null",
  "acquisition_method": "sba_7a | seller_finance | sba_plus_seller_carry",
  "exit_signals": ["signal1", "signal2"],
  "notes": "brief analysis"
}}

Return ONLY a JSON array. If nothing viable, return [].
"""
    return ask_json(prompt, BIZ_SYSTEM)


def write_biz_email(lead: dict, sender_name: str = "Kalob") -> Optional[dict]:
    """Write outreach email to a business owner about acquisition."""
    prompt = f"""
Write a genuine, concise email to a small business owner in Northern Michigan
about exploring whether they'd ever consider selling their business.

Business details:
- Business: {lead.get('name')}
- Type: {lead.get('business_type', 'business')}
- City: {lead.get('city', 'Northern Michigan')}
- Owner: {lead.get('owner_name', 'Business Owner')}
- Acquisition method I'm considering: {lead.get('acquisition_method', 'SBA loan + seller carry')}
- My name: {sender_name}

Requirements:
- 120-160 words max
- Sound like a real person from the area, not a PE firm
- Acknowledge they may not be looking to sell (low pressure)
- Briefly mention I have financing flexibility (SBA + seller carry options)
- One genuine question at the end
- Mention Northern Michigan / the local community naturally
- NOT generic, NOT corporate-sounding

Return JSON:
{{
  "subject": "subject line",
  "body": "email body"
}}
"""
    return ask_json(prompt, BIZ_SYSTEM)


def score_deal(lead: dict, lead_type: str) -> int:
    """Quick AI scoring of a deal 1-10."""
    prompt = f"""
Score this {lead_type} acquisition opportunity from 1-10 based on:
- Creative financing viability
- Motivated seller signals
- Location quality (Northern Michigan)
- Cash flow potential

Lead data: {json.dumps(lead, indent=2)}

Respond with ONLY a single integer 1-10.
"""
    result = ask(prompt)
    if result:
        match = re.search(r"\b([1-9]|10)\b", result)
        if match:
            return int(match.group())
    return 5
