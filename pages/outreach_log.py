import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_outreach


def render():
    st.markdown('<div class="section-title">📬 Outreach Log</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    Complete history of all outreach emails — owner name, email, subject, full body,
    date/time sent, lead type, and delivery status.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Filter by Type", ["All", "Real Estate", "Business"], key="log_filter_type")
    with col2:
        filter_status = st.selectbox("Filter by Status", ["All", "sent", "replied", "skipped", "error"], key="log_filter_status")
    with col3:
        show_bodies = st.toggle("Show Email Bodies", value=False, key="log_show_bodies")

    # Load data
    lead_type_map = {"All": None, "Real Estate": "real_estate", "Business": "business"}
    outreach = get_outreach(lead_type=lead_type_map[filter_type], limit=500)

    if filter_status != "All":
        outreach = [o for o in outreach if o.get("status") == filter_status]

    if not outreach:
        st.markdown('<div class="info-box">No outreach records found.</div>', unsafe_allow_html=True)
        return

    # Summary row
    total = len(outreach)
    sent = sum(1 for o in outreach if o.get("status") in ["sent", "delivered"])
    replied = sum(1 for o in outreach if o.get("status") == "replied")
    simulated = sum(1 for o in outreach if o.get("simulated"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", total)
    c2.metric("Sent / Delivered", sent)
    c3.metric("Replied", replied)
    c4.metric("Simulated", simulated)

    st.markdown("<br>", unsafe_allow_html=True)

    # Export to CSV
    if st.button("⬇️ Export to CSV", key="export_csv"):
        df = pd.DataFrame(outreach)
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            data=csv,
            file_name=f"outreach_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_csv"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Records
    for item in outreach:
        sent_at = item.get("sent_at", "")
        if sent_at:
            try:
                dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
                sent_str = dt.strftime("%A, %B %d %Y at %I:%M %p UTC")
                short_time = dt.strftime("%m/%d/%y %I:%M %p")
            except Exception:
                sent_str = sent_at
                short_time = sent_at
        else:
            sent_str = "—"
            short_time = "—"

        status = item.get("status", "sent")
        badge_map = {
            "sent": ("badge-sent", "SENT"),
            "delivered": ("badge-sent", "DELIVERED"),
            "replied": ("badge-replied", "REPLIED"),
            "skipped": ("badge-skipped", "SKIPPED"),
            "error": ("badge-skipped", "ERROR"),
            "pending": ("badge-pending", "PENDING"),
        }
        badge_class, badge_label = badge_map.get(status, ("badge-pending", status.upper()))

        simulated = item.get("simulated", False)
        type_icon = "🏠" if item.get("lead_type") == "real_estate" else "🏢"
        sim_tag = ' <span style="color:#8899aa;font-size:0.7rem;">(simulated)</span>' if simulated else ""

        header = f"{type_icon} {item.get('owner_name') or 'Unknown Owner'} — {item.get('owner_email','No email')} — {short_time}"

        with st.expander(header, expanded=False):
            col_a, col_b = st.columns([2, 1])

            with col_a:
                st.markdown(f"**Owner:** {item.get('owner_name') or '—'}")
                st.markdown(f"**Email:** {item.get('owner_email') or '—'}")
                st.markdown(f"**Subject:** {item.get('subject') or '—'}")

            with col_b:
                st.markdown(f"**Sent:** {short_time}")
                st.markdown(
                    f"**Status:** <span class='status-badge {badge_class}'>{badge_label}</span>{sim_tag}",
                    unsafe_allow_html=True
                )
                st.markdown(f"**Type:** {item.get('lead_type','—').replace('_',' ').title()}")
                if item.get("gmail_message_id"):
                    st.markdown(f"**Gmail ID:** `{item['gmail_message_id'][:16]}...`")

            if show_bodies and item.get("body"):
                st.markdown("**Email Body:**")
                st.markdown(
                    f'<div style="background:#0a1628;border:1px solid #B8860B22;border-radius:6px;padding:1rem;font-size:0.85rem;color:#c8d8e8;white-space:pre-wrap;line-height:1.6;">{item["body"]}</div>',
                    unsafe_allow_html=True
                )

            if item.get("notes"):
                st.markdown(f"**Notes:** {item['notes']}")

            # Mark as replied
            if status not in ["replied"] and item.get("id"):
                if st.button("✅ Mark as Replied", key=f"mark_replied_{item['id']}"):
                    from utils.database import get_client
                    client = get_client()
                    if client:
                        client.table("outreach").update({"status": "replied"}).eq("id", item["id"]).execute()
                    st.success("Marked as replied!")
                    st.rerun()
