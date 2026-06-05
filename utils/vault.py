"""
Obsidian vault writer.
Writes each lead as a markdown note with YAML frontmatter and wikilinks.
Hub notes for cities, deal types, and owners are auto-created so the
Obsidian graph view shows meaningful clusters.

To use: open the vault/ folder in Obsidian ("Open folder as vault").
"""

import re
import json
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path(__file__).parent.parent / "vault"
LEADS_DIR = VAULT_DIR / "leads"
DEMO_DIR = VAULT_DIR / "leads" / "demo"
HUBS_DIR = VAULT_DIR / "_hubs"


def _safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*#\[\]]', '', name)
    name = re.sub(r'\s+', '-', name.strip())
    return name[:80]


def _ensure_dirs():
    LEADS_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    HUBS_DIR.mkdir(parents=True, exist_ok=True)


def _hub_note(name: str, hub_type: str) -> None:
    """Create a hub note if it doesn't exist yet."""
    path = HUBS_DIR / f"{_safe_filename(name)}.md"
    if not path.exists():
        labels = {
            "city": "All leads in this city link here.",
            "deal_type": "All leads with this deal structure link here.",
            "owner": "All leads connected to this person link here.",
        }
        desc = labels.get(hub_type, "Hub note.")
        path.write_text(
            f"# {name}\n\n*{desc}*\n\n"
            "Use the Obsidian graph view to see all connected leads.\n",
            encoding="utf-8",
        )


def _score_bar(score: int) -> str:
    score = max(0, min(10, int(score)))
    return "█" * score + "░" * (10 - score)


def write_lead(lead: dict, demo: bool = False) -> None:
    """Write or overwrite a lead's markdown note in the vault.
    Demo leads go to leads/demo/, real leads go to leads/.
    """
    try:
        _ensure_dirs()
        target_dir = DEMO_DIR if demo else LEADS_DIR

        name = lead.get("name", "Unknown Lead")
        lead_type = lead.get("type", "unknown")
        city = lead.get("city", "")
        owner = lead.get("owner_name") or ""
        score = lead.get("score", 0)
        status = lead.get("status", "new")
        address = lead.get("address") or "—"
        owner_email = lead.get("owner_email") or "—"
        owner_phone = lead.get("owner_phone") or "—"
        source = lead.get("source") or "—"
        notes = lead.get("notes") or "—"

        details = lead.get("details") or {}
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {}

        if lead_type == "real_estate":
            deal_type = details.get("deal_type") or lead.get("deal_type") or "unknown"
            asking_price = details.get("price_asking") or lead.get("price_asking") or ""
            signals = details.get("motivated_signals") or lead.get("motivated_signals") or []
            signals_label = "Motivated Signals"
            extra_lines = f"- **Asking Price**: {asking_price}\n" if asking_price else ""
        else:
            deal_type = details.get("acquisition_method") or lead.get("acquisition_method") or "unknown"
            asking_price = details.get("asking_price") or lead.get("asking_price") or ""
            annual_revenue = details.get("annual_revenue") or lead.get("annual_revenue") or ""
            biz_type = details.get("business_type") or lead.get("business_type") or ""
            signals = details.get("exit_signals") or lead.get("exit_signals") or []
            signals_label = "Exit Signals"
            extra_lines = "".join(filter(None, [
                f"- **Business Type**: {biz_type}\n" if biz_type else "",
                f"- **Asking Price**: {asking_price}\n" if asking_price else "",
                f"- **Annual Revenue**: {annual_revenue}\n" if annual_revenue else "",
            ]))

        # Create hub notes for graph clustering
        if city:
            _hub_note(city, "city")
        if deal_type and deal_type != "unknown":
            _hub_note(deal_type, "deal_type")
        if owner:
            _hub_note(owner, "owner")

        city_link = f"[[{city}]]" if city else "—"
        owner_link = f"[[{owner}]]" if owner else "—"
        deal_link = f"[[{deal_type}]]" if deal_type and deal_type != "unknown" else deal_type
        signals_md = "\n".join(f"- {s}" for s in signals) if signals else "- None identified"

        frontmatter = (
            "---\n"
            f"score: {score}\n"
            f"type: {lead_type}\n"
            f"deal_type: {deal_type}\n"
            f"city: \"{city}\"\n"
            f"owner: \"{owner or 'Unknown'}\"\n"
            f"status: {status}\n"
            f"updated: {datetime.now().strftime('%Y-%m-%d')}\n"
            "---\n"
        )

        body = (
            f"# {name}\n\n"
            f"**Score**: {score}/10  `{_score_bar(score)}`\n"
            f"**City**: {city_link} | **Deal Type**: {deal_link} | **Status**: {status}\n\n"
            "---\n\n"
            "## Details\n"
            f"- **Owner**: {owner_link}\n"
            f"- **Email**: {owner_email}\n"
            f"- **Phone**: {owner_phone}\n"
            f"- **Address**: {address}\n"
            f"- **Source**: {source}\n"
            f"{extra_lines}\n"
            f"## {signals_label}\n"
            f"{signals_md}\n\n"
            "## AI Analysis\n"
            f"{notes}\n\n"
            "## Outreach Log\n"
            "<!-- Emails sent to this lead will be logged here -->\n\n"
            "## My Notes\n"
            "<!-- Add follow-up reminders, conversation notes, etc. -->\n"
        )

        filename = f"{_safe_filename(name)}.md"
        (target_dir / filename).write_text(frontmatter + "\n" + body, encoding="utf-8")

    except Exception:
        pass  # Never let vault errors break the main app


def log_outreach_to_vault(lead_name: str, subject: str, body: str, sent_at: str = "") -> None:
    """Append an outreach entry to an existing lead's vault note."""
    try:
        filename = f"{_safe_filename(lead_name)}.md"
        path = LEADS_DIR / filename
        if not path.exists():
            return
        content = path.read_text(encoding="utf-8")
        timestamp = sent_at or datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = (
            f"\n### {timestamp}\n"
            f"**Subject**: {subject}\n\n"
            f"{body}\n"
        )
        content = content.replace(
            "<!-- Emails sent to this lead will be logged here -->",
            f"<!-- Emails sent to this lead will be logged here -->{entry}"
        )
        path.write_text(content, encoding="utf-8")
    except Exception:
        pass
