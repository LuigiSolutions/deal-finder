import streamlit as st
import time
from datetime import datetime
from utils import gemini, scraper, database, gmail_sender


def render():
    st.markdown('<div class="section-title">🏠 Real Estate Acquisition Agent</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    This agent searches Northern Michigan for motivated sellers and off-market real estate deals
    suitable for creative financing: seller financing, subject-to, lease-option, or DSCR loans.
    It then drafts and sends personalized outreach emails to owners.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["▶  Run Agent", "📋  Leads"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            city = st.selectbox(
                "Target City",
                scraper.NMI_CITIES,
                index=0,
                key="re_city"
            )

            deal_types = st.multiselect(
                "Deal Types to Target",
                ["Seller Financing", "Subject-To", "Lease Option", "DSCR / Income Property", "FSBO"],
                default=["Seller Financing", "FSBO", "DSCR / Income Property"],
                key="re_deal_types"
            )

            min_score = st.slider("Minimum Deal Score to Auto-Contact", 1, 10, 7, key="re_min_score")

        with col2:
            auto_email = st.toggle("Auto-send emails to qualifying leads", value=False, key="re_auto_email")

            if auto_email:
                st.markdown("""
                <div style="background:#3a1a00;border:1px solid #FFD70044;border-radius:6px;padding:0.7rem;font-size:0.82rem;color:#FFD700;">
                ⚠️ Auto-send is ON. Emails will send immediately to owners with score ≥ {}.
                Review leads first if you prefer manual approval.
                </div>
                """.format(min_score), unsafe_allow_html=True)

            use_demo = st.toggle("Use demo data (no API needed)", value=True, key="re_demo")
            st.caption("Turn off demo mode once your API keys are configured.")

        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("🔍  Search for Real Estate Deals", key="re_run", use_container_width=True)

        if run_btn:
            _run_re_agent(city, auto_email, min_score, use_demo)

    with tab2:
        _show_re_leads()


def _run_re_agent(city: str, auto_email: bool, min_score: int, use_demo: bool):
    sender_name = st.secrets.get("YOUR_NAME", "Kalob") if hasattr(st, "secrets") else "Kalob"

    log_lines = []
    leads_found = 0
    emails_sent = 0

    with st.status("Running Real Estate Agent...", expanded=True) as status:

        # Step 1: Gather data
        st.write(f"🔎 Searching for deals in {city}...")
        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting RE agent for {city}")

        if use_demo:
            raw_leads = scraper.get_demo_re_leads()
            st.write(f"✅ Demo mode: loaded {len(raw_leads)} sample leads")
        else:
            st.write("  Scraping Craigslist FSBO + web search...")
            search_data = scraper.get_re_search_data(city)
            st.write("  Sending to Gemini for lead extraction...")
            raw_leads = gemini.generate_re_leads(search_data, city) or []
            st.write(f"✅ Gemini extracted {len(raw_leads)} potential leads")

        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(raw_leads)} raw leads")

        if not raw_leads:
            status.update(label="No leads found this run.", state="complete")
            return

        # Step 2: Save leads
        st.write("💾 Saving leads to database...")
        saved_leads = []
        for lead in raw_leads:
            lead["type"] = "real_estate"
            # Nest extra fields in details
            details = {k: v for k, v in lead.items() if k not in [
                "type", "name", "address", "city", "owner_name", "owner_email",
                "owner_phone", "source", "source_url", "score", "status", "notes"
            ]}
            lead["details"] = details
            saved = database.upsert_lead(lead)
            if saved:
                saved_leads.append({**lead, **(saved if isinstance(saved, dict) else {})})
                leads_found += 1

        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Saved {leads_found} leads")

        # Step 3: Email qualifying leads
        qualifying = sorted(
            [l for l in raw_leads if l.get("score", 0) >= min_score and l.get("owner_email")],
            key=lambda l: l.get("score", 0),
            reverse=True
        )

        if auto_email and qualifying:
            st.write(f"📬 Writing and sending emails to {len(qualifying)} qualifying leads (score ≥ {min_score})...")
            for lead in qualifying:
                if database.has_been_contacted(lead["owner_email"]):
                    st.write(f"  ⏭️ Skipping {lead['owner_email']} — already contacted")
                    continue

                # Generate email
                email_data = gemini.write_re_email(lead, sender_name)
                if not email_data:
                    st.write(f"  ⚠️ Could not generate email for {lead.get('name')}")
                    continue

                result = gmail_sender.send_email(
                    to_email=lead["owner_email"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    from_name=sender_name,
                )

                sim_note = " (simulated — Gmail not configured)" if result.get("simulated") else ""
                st.write(f"  ✉️ Sent to {lead['owner_name'] or lead['owner_email']}{sim_note}")

                database.log_outreach({
                    "lead_type": "real_estate",
                    "owner_name": lead.get("owner_name"),
                    "owner_email": lead["owner_email"],
                    "subject": email_data["subject"],
                    "body": email_data["body"],
                    "status": "sent" if result["success"] else "error",
                    "gmail_message_id": result.get("message_id"),
                    "simulated": result.get("simulated", False),
                    "notes": result.get("error"),
                })
                emails_sent += 1
                time.sleep(2)  # Rate limit: 15 req/min on Gemini free tier
        elif not auto_email:
            st.write(f"📋 Found {leads_found} leads. Auto-email is OFF — review leads in the Leads tab.")
        else:
            st.write(f"📋 {leads_found} leads found but none had emails + score ≥ {min_score}.")

        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {emails_sent} emails")
        status.update(
            label=f"✅ Done — {leads_found} leads found, {emails_sent} emails sent",
            state="complete"
        )

    # Summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Leads Found", leads_found)
    col2.metric("Emails Sent", emails_sent)
    col3.metric("Qualifying Leads", len(qualifying) if auto_email else "N/A (manual mode)")


def _show_re_leads():
    leads = database.get_leads(lead_type="real_estate", limit=50)

    if not leads:
        st.markdown('<div class="info-box">No real estate leads yet. Run the agent above.</div>', unsafe_allow_html=True)
        return

    st.markdown(f"**{len(leads)} real estate leads found**")
    st.markdown("<br>", unsafe_allow_html=True)

    for lead in leads:
        score = lead.get("score", 0)
        score_color = "#4caf50" if score >= 7 else "#FFD700" if score >= 5 else "#ef5350"
        details = lead.get("details", {}) or {}
        if isinstance(details, str):
            import json
            try:
                details = json.loads(details)
            except Exception:
                details = {}

        with st.expander(f"🏠 {lead.get('name','Unknown')} — Score: {score}/10 — {lead.get('city','')}", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Owner:** {lead.get('owner_name') or '—'}")
            c1.markdown(f"**Email:** {lead.get('owner_email') or '—'}")
            c1.markdown(f"**Phone:** {lead.get('owner_phone') or '—'}")
            c2.markdown(f"**Address:** {lead.get('address','—')}")
            c2.markdown(f"**Deal Type:** {details.get('deal_type', lead.get('deal_type','—'))}")
            c2.markdown(f"**Asking Price:** {details.get('price_asking', lead.get('price_asking','—'))}")
            c3.markdown(f"**Source:** {lead.get('source','—')}")
            c3.markdown(f"**Status:** {lead.get('status','new')}")

            signals = details.get("motivated_signals", lead.get("motivated_signals", []))
            if signals:
                st.markdown(f"**Motivated Signals:** {' · '.join(signals)}")

            if lead.get("notes"):
                st.markdown(f"**AI Notes:** {lead['notes']}")

            # Manual email button
            if lead.get("owner_email"):
                sender_name = st.secrets.get("YOUR_NAME", "Kalob") if hasattr(st, "secrets") else "Kalob"
                if not database.has_been_contacted(lead["owner_email"]):
                    if st.button(f"📬 Write & Send Email", key=f"re_send_{lead.get('id', lead.get('name',''))}"):
                        with st.spinner("Writing personalized email..."):
                            email_data = gemini.write_re_email(lead, sender_name)
                        if email_data:
                            st.markdown(f"**Subject:** {email_data['subject']}")
                            st.text_area("Email Body", email_data["body"], height=180,
                                         key=f"re_body_{lead.get('id', lead.get('name',''))}")
                            if st.button("✅ Confirm & Send", key=f"re_confirm_{lead.get('id', lead.get('name',''))}"):
                                result = gmail_sender.send_email(lead["owner_email"], email_data["subject"], email_data["body"])
                                database.log_outreach({
                                    "lead_type": "real_estate",
                                    "owner_name": lead.get("owner_name"),
                                    "owner_email": lead["owner_email"],
                                    "subject": email_data["subject"],
                                    "body": email_data["body"],
                                    "status": "sent" if result["success"] else "error",
                                    "simulated": result.get("simulated", False),
                                })
                                st.success("Email sent!" if result["success"] else f"Error: {result['error']}")
                else:
                    st.markdown('<span style="color:#4caf50;font-size:0.85rem;">✅ Already contacted</span>', unsafe_allow_html=True)
