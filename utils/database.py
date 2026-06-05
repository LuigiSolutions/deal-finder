"""
Supabase database layer — free tier (500MB, unlimited API calls)
All tables auto-created on first run via SQL migration
"""

import streamlit as st
from datetime import datetime
from typing import Optional
import json

from utils.vault import write_lead as _vault_write_lead, log_outreach_to_vault as _vault_log_outreach

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


def get_client() -> Optional[object]:
    """Return Supabase client if credentials are configured."""
    if not SUPABASE_AVAILABLE:
        return None
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


# ── SQL to run once in Supabase SQL Editor ─────────────────────────────────────
SETUP_SQL = """
-- Leads table: one row per discovered property or business
CREATE TABLE IF NOT EXISTS leads (
    id            BIGSERIAL PRIMARY KEY,
    type          TEXT NOT NULL CHECK (type IN ('real_estate', 'business')),
    name          TEXT NOT NULL,
    owner_name    TEXT,
    owner_email   TEXT,
    owner_phone   TEXT,
    address       TEXT,
    city          TEXT DEFAULT 'Northern Michigan',
    state         TEXT DEFAULT 'MI',
    details       JSONB,          -- flexible: price, sqft, business type, revenue, etc.
    source        TEXT,           -- where we found it
    source_url    TEXT,
    score         INT DEFAULT 0,  -- AI deal score 1-10
    status        TEXT DEFAULT 'new' CHECK (status IN ('new','contacted','replied','passed','closed')),
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Outreach table: every email/message sent
CREATE TABLE IF NOT EXISTS outreach (
    id            BIGSERIAL PRIMARY KEY,
    lead_id       BIGINT REFERENCES leads(id) ON DELETE CASCADE,
    lead_type     TEXT NOT NULL,
    owner_name    TEXT,
    owner_email   TEXT,
    subject       TEXT,
    body          TEXT NOT NULL,
    sent_at       TIMESTAMPTZ DEFAULT NOW(),
    status        TEXT DEFAULT 'sent' CHECK (status IN ('sent','delivered','opened','replied','bounced','skipped')),
    gmail_message_id TEXT,
    notes         TEXT
);

-- Agent runs: log of every agent execution
CREATE TABLE IF NOT EXISTS agent_runs (
    id            BIGSERIAL PRIMARY KEY,
    agent_type    TEXT NOT NULL,
    started_at    TIMESTAMPTZ DEFAULT NOW(),
    finished_at   TIMESTAMPTZ,
    leads_found   INT DEFAULT 0,
    emails_sent   INT DEFAULT 0,
    status        TEXT DEFAULT 'running',
    error_message TEXT,
    log           TEXT
);

-- Index for fast filtering
CREATE INDEX IF NOT EXISTS leads_type_idx    ON leads(type);
CREATE INDEX IF NOT EXISTS leads_status_idx  ON leads(status);
CREATE INDEX IF NOT EXISTS outreach_lead_idx ON outreach(lead_id);
CREATE INDEX IF NOT EXISTS outreach_sent_idx ON outreach(sent_at DESC);
"""


# ── LEAD OPERATIONS ────────────────────────────────────────────────────────────

def upsert_lead(data: dict) -> Optional[dict]:
    """Insert a lead or update if name+address already exists."""
    is_demo = data.pop("is_demo", False)
    _vault_write_lead(data, demo=is_demo)

    client = get_client()
    if not client:
        return _local_store("leads", data)

    # Check duplicate
    existing = (
        client.table("leads")
        .select("id")
        .eq("name", data.get("name", ""))
        .eq("address", data.get("address", ""))
        .execute()
    )
    if existing.data:
        row_id = existing.data[0]["id"]
        data["updated_at"] = datetime.utcnow().isoformat()
        result = client.table("leads").update(data).eq("id", row_id).execute()
        return result.data[0] if result.data else None

    result = client.table("leads").insert(data).execute()
    return result.data[0] if result.data else None


def get_leads(lead_type: str = None, status: str = None, limit: int = 200) -> list:
    client = get_client()
    if not client:
        return _local_read("leads")

    query = client.table("leads").select("*").order("score", desc=True).order("created_at", desc=True).limit(limit)
    if lead_type:
        query = query.eq("type", lead_type)
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return result.data or []


def update_lead_status(lead_id: int, status: str, notes: str = None):
    client = get_client()
    if not client:
        return
    update = {"status": status, "updated_at": datetime.utcnow().isoformat()}
    if notes:
        update["notes"] = notes
    client.table("leads").update(update).eq("id", lead_id).execute()


# ── OUTREACH OPERATIONS ────────────────────────────────────────────────────────

def log_outreach(data: dict) -> Optional[dict]:
    """Record every email sent."""
    _vault_log_outreach(
        lead_name=data.get("owner_name") or data.get("lead_type", "lead"),
        subject=data.get("subject", ""),
        body=data.get("body", ""),
    )

    client = get_client()
    if not client:
        return _local_store("outreach", data)

    result = client.table("outreach").insert(data).execute()
    return result.data[0] if result.data else None


def get_outreach(lead_type: str = None, limit: int = 200) -> list:
    client = get_client()
    if not client:
        return _local_read("outreach")

    query = client.table("outreach").select("*").order("sent_at", desc=True).limit(limit)
    if lead_type:
        query = query.eq("lead_type", lead_type)
    result = query.execute()
    return result.data or []


def has_been_contacted(owner_email: str) -> bool:
    """Prevent double-emailing the same owner."""
    client = get_client()
    if not client:
        sent = _local_read("outreach")
        return any(r.get("owner_email") == owner_email for r in sent)

    result = (
        client.table("outreach")
        .select("id")
        .eq("owner_email", owner_email)
        .execute()
    )
    return bool(result.data)


# ── AGENT RUN LOGGING ──────────────────────────────────────────────────────────

def start_agent_run(agent_type: str) -> Optional[int]:
    client = get_client()
    if not client:
        return None
    result = client.table("agent_runs").insert({"agent_type": agent_type, "status": "running"}).execute()
    return result.data[0]["id"] if result.data else None


def finish_agent_run(run_id: int, leads_found: int, emails_sent: int, log: str, error: str = None):
    client = get_client()
    if not client:
        return
    client.table("agent_runs").update({
        "finished_at": datetime.utcnow().isoformat(),
        "leads_found": leads_found,
        "emails_sent": emails_sent,
        "status": "error" if error else "completed",
        "error_message": error,
        "log": log
    }).eq("id", run_id).execute()


def get_stats() -> dict:
    client = get_client()
    if not client:
        leads = _local_read("leads")
        outreach = _local_read("outreach")
        return {
            "total_leads": len(leads),
            "re_leads": sum(1 for l in leads if l.get("type") == "real_estate"),
            "biz_leads": sum(1 for l in leads if l.get("type") == "business"),
            "emails_sent": len(outreach),
            "replied": sum(1 for o in outreach if o.get("status") == "replied"),
        }

    leads = client.table("leads").select("id, type, status").execute().data or []
    outreach = client.table("outreach").select("id, status").execute().data or []
    return {
        "total_leads": len(leads),
        "re_leads": sum(1 for l in leads if l.get("type") == "real_estate"),
        "biz_leads": sum(1 for l in leads if l.get("type") == "business"),
        "emails_sent": len(outreach),
        "replied": sum(1 for o in outreach if o.get("status") == "replied"),
    }


# ── LOCAL FALLBACK (session state when Supabase not configured) ────────────────

def _local_store(table: str, data: dict) -> dict:
    if table not in st.session_state:
        st.session_state[table] = []
    data["id"] = len(st.session_state[table]) + 1
    data.setdefault("created_at", datetime.utcnow().isoformat())
    st.session_state[table].append(data)
    return data


def _local_read(table: str) -> list:
    return st.session_state.get(table, [])
