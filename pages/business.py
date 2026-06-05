import streamlit as st
import time
from datetime import datetime
from utils import gemini, scraper, database, gmail_sender


def render():
    st.markdown('<div class="section-title">🏢 Business Acquisition Agent</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    This agent searches Northern Michigan for owner-operated businesses that can be acquired using
    SBA 7(a) loans (90% bank-financed on business cashflow), seller financing, or a combination
    of both — often achieving near-zero out-of-pocket acquisition.
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
                key="biz_city"
            )

            sectors = st.multiselect(
                "Target Business Sectors",
                [
                    "HVAC / Plumbing / Electrical",
                    "Auto Repair / Automotive",
                    "Restaurant / Food Service",
                    "Landscaping / Lawn Care",
                    "Laundromat / Dry Cleaning",
                    "Retail / Hardware",
                    "Healthcare / Dental / Chiro",
                    "Accounting / Tax",
                    "Insurance Agency",
                    "Any / All Sectors",
                ],
                default=["HVAC / Plumbing / Electrical", "Auto Repair / Automotive", "Laundromat / Dry Cleaning"],
                key="biz_sectors"
            )

            min_score = st.slider("Minimum Deal Score to Auto-Contact", 1, 10, 7, key="biz_min_score")

        with col2:
            acquisition_focus = st.selectbox(
                "Primary Acquisition Method",
                ["SBA 7(a) + Seller Carry (near-zero down)", "Seller Financing Only", "SBA 7(a) Only"],
                key="biz_acq_method"
            )

            auto_email = st.toggle("Auto-send emails to qualifying leads", value=False, key="biz_auto_email")

            if auto_email:
                st.markdown("""
                <div style="background:#3a1a00;border:1px solid #FFD70044;border-radius:6px;padding:0.7rem;font-size:0.82rem;color:#FFD700;">
                ⚠️ Auto-send is ON. Emails will go to owners with score ≥ {}.
                </div>
                """.format(min_score), unsafe_allow_html=True)

            use_demo = st.toggle("Use demo data (no API needed)", value=True, key="biz_demo")
            st.caption("Turn off demo mode once your API keys are configured.")

        st.markdown("""
        <div style="background:#0F1B2D;border:1px solid #B8860B33;border-radius:8px;padding:1rem;margin-top:1rem;font-size:0.85rem;">
        <strong style="color:#B8860B;">How SBA 7(a) + Seller Carry Works</strong><br><br>
        <span style="color:#aab8c8;">
        1. You find a business doing $500K+ revenue with consistent profitability<br>
        2. Asking price: $350K<br>
        3. SBA 7(a) covers 90% = <strong style="color:#e8e0d0;">$315,000</strong> (bank lending based on business cashflow, not your income)<br>
        4. Seller carries 10% as a note = <strong style="color:#e8e0d0;">$35,000</strong> paid over time from business revenue<br>
        5. You're in for <strong style="color:#4caf50;">$0–$10K out of pocket</strong> (SBA fees + closing costs)<br>
        6. Business cash flow pays all debt service
        </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("🔍  Search for Business Acquisition Targets", key="biz_run", use_container_width=True)

        if run_btn:
            _run_biz_agent(city, auto_email, min_score, use_demo, sectors, acquisition_focus)

    with tab2:
        _show_biz_leads()


def _run_biz_agent(city: str, auto_email: bool, min_score: int, use_demo: bool, sectors: list, acq_method: str):
    sender_name = st.secrets.get("YOUR_NAME", "Kalob") if hasattr(st, "secrets") else "Kalob"

    log_lines = []
    leads_found = 0
    emails_sent = 0
    qualifying = []

    with st.status("Running Business Acquisition Agent...", expanded=True) as status:

        st.write(f"🔎 Searching for businesses in {city}...")
        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Biz agent for {city}")

        if use_demo:
            raw_leads = scraper.get_demo_biz_leads()
            st.write(f"✅ Demo mode: loaded {len(raw_leads)} sample leads")
        else:
            st.write("  Scraping BizBuySell + web search...")
            search_data = scraper.get_biz_search_data(city)
            st.write("  Sending to Gemini for extraction...")
            raw_leads = gemini.generate_biz_leads(search_data, city) or []
            st.write(f"✅ Gemini extracted {len(raw_leads)} potential leads")

        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(raw_leads)} raw leads")

        if not raw_leads:
            status.update(label="No leads found this run.", state="complete")
            return

        # Save
        st.write("💾 Saving to database...")
        for lead in raw_leads:
            lead["type"] = "business"
            lead["is_demo"] = use_demo
            details = {k: v for k, v in lead.items() if k not in [
                "type", "name", "address", "city", "owner_name", "owner_email",
                "owner_phone", "source", "source_url", "score", "status", "notes"
            ]}
            lead["details"] = details
            saved = database.upsert_lead(lead)
            if saved:
                leads_found += 1

        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Saved {leads_found} leads")

        # Email qualifying
        qualifying = sorted(
            [l for l in raw_leads if l.get("score", 0) >= min_score and l.get("owner_email")],
            key=lambda l: l.get("score", 0),
            reverse=True
        )

        if auto_email and qualifying:
            st.write(f"📬 Writing and sending emails to {len(qualifying)} qualifying leads...")
            for lead in qualifying:
                if database.has_been_contacted(lead["owner_email"]):
                    st.write(f"  ⏭️ Skipping {lead['owner_email']} — already contacted")
                    continue

                email_data = gemini.write_biz_email(lead, sender_name)
                if not email_data:
                    continue

                result = gmail_sender.send_email(
                    to_email=lead["owner_email"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    from_name=sender_name,
                )

                sim_note = " (simulated)" if result.get("simulated") else ""
                st.write(f"  ✉️ Sent to {lead.get('owner_name') or lead['owner_email']}{sim_note}")

                database.log_outreach({
                    "lead_type": "business",
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
                time.sleep(2)
        elif not auto_email:
            st.write(f"📋 {leads_found} leads saved. Auto-email is OFF — go to Leads tab to review and send manually.")
        else:
            st.write(f"📋 {leads_found} leads saved but none had email + score ≥ {min_score}.")

        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {emails_sent} emails")
        status.update(
            label=f"✅ Done — {leads_found} leads found, {emails_sent} emails sent",
            state="complete"
        )

    col1, col2, col3 = st.columns(3)
    col1.metric("Leads Found", leads_found)
    col2.metric("Emails Sent", emails_sent)
    col3.metric("Qualifying (score ≥ {})".format(min_score), len(qualifying))


def _show_biz_leads():
    leads = database.get_leads(lead_type="business", limit=50)

    if not leads:
        st.markdown('<div class="info-box">No business leads yet. Run the agent above.</div>', unsafe_allow_html=True)
        return

    st.markdown(f"**{len(leads)} business acquisition leads**")
    st.markdown("<br>", unsafe_allow_html=True)

    for lead in leads:
        score = lead.get("score", 0)
        details = lead.get("details", {}) or {}
        if isinstance(details, str):
            import json
            try:
                details = json.loads(details)
            except Exception:
                details = {}

        biz_type = details.get("business_type", lead.get("business_type", "Business"))

        with st.expander(f"🏢 {lead.get('name','Unknown')} ({biz_type}) — Score: {score}/10 — {lead.get('city','')}", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Owner:** {lead.get('owner_name') or '—'}")
            c1.markdown(f"**Email:** {lead.get('owner_email') or '—'}")
            c1.markdown(f"**Phone:** {lead.get('owner_phone') or '—'}")
            c2.markdown(f"**Asking Price:** {details.get('asking_price', lead.get('asking_price','—'))}")
            c2.markdown(f"**Annual Revenue:** {details.get('annual_revenue', lead.get('annual_revenue','—'))}")
            c2.markdown(f"**Acq. Method:** {details.get('acquisition_method', lead.get('acquisition_method','—'))}")
            c3.markdown(f"**Source:** {lead.get('source','—')}")
            c3.markdown(f"**Status:** {lead.get('status','new')}")

            signals = details.get("exit_signals", lead.get("exit_signals", []))
            if signals:
                st.markdown(f"**Exit Signals:** {' · '.join(signals)}")

            if lead.get("notes"):
                st.markdown(f"**AI Notes:** {lead['notes']}")

            if lead.get("owner_email"):
                sender_name = st.secrets.get("YOUR_NAME", "Kalob") if hasattr(st, "secrets") else "Kalob"
                if not database.has_been_contacted(lead["owner_email"]):
                    if st.button("📬 Write & Send Email", key=f"biz_send_{lead.get('id', lead.get('name',''))}"):
                        with st.spinner("Writing email..."):
                            email_data = gemini.write_biz_email(lead, sender_name)
                        if email_data:
                            st.markdown(f"**Subject:** {email_data['subject']}")
                            st.text_area("Email Body", email_data["body"], height=200,
                                         key=f"biz_body_{lead.get('id', lead.get('name',''))}")
                            if st.button("✅ Confirm & Send", key=f"biz_confirm_{lead.get('id', lead.get('name',''))}"):
                                result = gmail_sender.send_email(lead["owner_email"], email_data["subject"], email_data["body"])
                                database.log_outreach({
                                    "lead_type": "business",
                                    "owner_name": lead.get("owner_name"),
                                    "owner_email": lead["owner_email"],
                                    "subject": email_data["subject"],
                                    "body": email_data["body"],
                                    "status": "sent" if result["success"] else "error",
                                    "simulated": result.get("simulated", False),
                                })
                                st.success("Sent!" if result["success"] else f"Error: {result['error']}")
                else:
                    st.markdown('<span style="color:#4caf50;font-size:0.85rem;">✅ Already contacted</span>', unsafe_allow_html=True)
