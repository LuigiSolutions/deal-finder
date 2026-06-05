import streamlit as st
from utils.database import get_stats, get_leads, get_outreach
from datetime import datetime


def render():
    stats = get_stats()

    # Metrics row
    cols = st.columns(5)
    metrics = [
        ("Total Leads", stats["total_leads"], "🎯"),
        ("RE Leads", stats["re_leads"], "🏠"),
        ("Biz Leads", stats["biz_leads"], "🏢"),
        ("Emails Sent", stats["emails_sent"], "📬"),
        ("Replied", stats["replied"], "💬"),
    ]
    for col, (label, value, icon) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.4rem;">{icon}</div>
                <div class="metric-number">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Recent Real Estate Leads</div>', unsafe_allow_html=True)
        re_leads = get_leads(lead_type="real_estate", limit=5)
        if re_leads:
            for lead in re_leads:
                score = lead.get("score", 0)
                score_color = "#4caf50" if score >= 7 else "#FFD700" if score >= 5 else "#ef5350"
                st.markdown(f"""
                <div class="deal-row">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div class="deal-name">{lead.get('name','Unknown')}</div>
                        <div style="color:{score_color};font-family:'Bebas Neue',sans-serif;font-size:1.1rem;">
                            {score}/10
                        </div>
                    </div>
                    <div class="deal-meta">
                        📍 {lead.get('city','—')} &nbsp;·&nbsp;
                        🏷️ {lead.get('details', {}).get('deal_type', lead.get('deal_type','—')) if isinstance(lead.get('details'), dict) else '—'} &nbsp;·&nbsp;
                        👤 {lead.get('owner_name') or 'Owner unknown'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">No real estate leads yet. Run the Real Estate Agent to find deals.</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-title">Recent Business Leads</div>', unsafe_allow_html=True)
        biz_leads = get_leads(lead_type="business", limit=5)
        if biz_leads:
            for lead in biz_leads:
                score = lead.get("score", 0)
                score_color = "#4caf50" if score >= 7 else "#FFD700" if score >= 5 else "#ef5350"
                st.markdown(f"""
                <div class="deal-row">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div class="deal-name">{lead.get('name','Unknown')}</div>
                        <div style="color:{score_color};font-family:'Bebas Neue',sans-serif;font-size:1.1rem;">
                            {score}/10
                        </div>
                    </div>
                    <div class="deal-meta">
                        📍 {lead.get('city','—')} &nbsp;·&nbsp;
                        🏢 {lead.get('details', {}).get('business_type', lead.get('business_type','—')) if isinstance(lead.get('details'), dict) else '—'} &nbsp;·&nbsp;
                        👤 {lead.get('owner_name') or 'Owner unknown'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">No business leads yet. Run the Business Agent to find deals.</div>', unsafe_allow_html=True)

    # Recent outreach
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Recent Outreach</div>', unsafe_allow_html=True)
    outreach = get_outreach(limit=8)
    if outreach:
        for item in outreach:
            sent_at = item.get("sent_at", "")
            if sent_at:
                try:
                    dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
                    sent_str = dt.strftime("%b %d, %Y %I:%M %p")
                except Exception:
                    sent_str = sent_at
            else:
                sent_str = "—"

            status = item.get("status", "sent")
            badge_map = {
                "sent": "badge-sent", "delivered": "badge-sent",
                "replied": "badge-replied", "skipped": "badge-skipped",
                "pending": "badge-pending"
            }
            badge_class = badge_map.get(status, "badge-pending")
            simulated = item.get("simulated", False)

            st.markdown(f"""
            <div class="deal-row">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
                    <div>
                        <span class="deal-name">{item.get('owner_name') or 'Unknown Owner'}</span>
                        <span class="deal-meta" style="margin-left:8px;">{item.get('owner_email','')}</span>
                    </div>
                    <div style="display:flex;gap:8px;align-items:center;">
                        <span class="status-badge {badge_class}">{status}{' (sim)' if simulated else ''}</span>
                        <span class="deal-meta">{sent_str}</span>
                    </div>
                </div>
                <div class="deal-meta" style="margin-top:4px;">📨 {item.get('subject','—')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">No outreach sent yet. Configure your agents and run them to start reaching out.</div>', unsafe_allow_html=True)

    # Setup checklist
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Setup Checklist</div>', unsafe_allow_html=True)

    try:
        has_gemini = bool(st.secrets.get("GEMINI_API_KEY", ""))
        has_supabase = bool(st.secrets.get("SUPABASE_URL", ""))
        has_gmail = bool(st.secrets.get("GMAIL_CREDENTIALS_JSON", ""))
        has_sender = bool(st.secrets.get("YOUR_NAME", ""))
    except Exception:
        has_gemini = has_supabase = has_gmail = has_sender = False

    checks = [
        (has_gemini, "Gemini Flash API key (free at aistudio.google.com)"),
        (has_supabase, "Supabase database (free at supabase.com)"),
        (has_gmail, "Gmail API credentials (free via Google Cloud Console)"),
        (has_sender, "Your name configured in Settings"),
    ]

    for done, label in checks:
        icon = "✅" if done else "⬜"
        color = "#4caf50" if done else "#8899aa"
        st.markdown(f'<div style="color:{color};padding:4px 0;font-size:0.9rem;">{icon} {label}</div>', unsafe_allow_html=True)
