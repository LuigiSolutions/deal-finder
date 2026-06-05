import streamlit as st
import streamlit.components.v1 as components
from utils import database

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False


def _score_color(score: int) -> str:
    if score >= 8:
        return "#4caf50"   # green
    if score >= 5:
        return "#FFD700"   # gold
    return "#ef5350"       # red


def _node_size(score: int) -> int:
    return 12 + int(score) * 2   # 14–32px


def render():
    st.markdown('<div class="section-title">🕸️ Knowledge Graph</div>', unsafe_allow_html=True)
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .graph-tip { display: block !important; }
    }
    .graph-tip { display: none; }
    </style>
    <div class="graph-tip info-box">
    Tip: graph works best in landscape mode on mobile. Pinch to zoom, drag to pan.
    </div>
    """, unsafe_allow_html=True)

    if not PYVIS_AVAILABLE:
        st.error("pyvis not installed — add `pyvis>=0.3.1` to requirements.txt and redeploy.")
        return

    mode = st.toggle("Show real leads (off = demo leads)", value=False, key="graph_mode")

    if mode:
        leads = database.get_leads(limit=200)
    else:
        from utils.scraper import get_demo_re_leads, get_demo_biz_leads
        leads = get_demo_re_leads() + get_demo_biz_leads()
        for l in leads:
            l.setdefault("type", "real_estate" if "motivated_signals" in l else "business")

    if not leads:
        st.markdown("""
        <div class="info-box">
        No leads yet. Run the Real Estate or Business agent first, then come back here.
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Legend ────────────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown('<span style="color:#4caf50;font-size:0.82rem;">● Score 8-10</span>', unsafe_allow_html=True)
    col2.markdown('<span style="color:#FFD700;font-size:0.82rem;">● Score 5-7</span>', unsafe_allow_html=True)
    col3.markdown('<span style="color:#ef5350;font-size:0.82rem;">● Score 1-4</span>', unsafe_allow_html=True)
    col4.markdown('<span style="color:#4fc3f7;font-size:0.82rem;">■ City hub</span>', unsafe_allow_html=True)
    col5.markdown('<span style="color:#B8860B;font-size:0.82rem;">◆ Deal type</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Build graph ───────────────────────────────────────────────────────────
    net = Network(
        height="620px",
        width="100%",
        bgcolor="#0F1B2D",
        font_color="#e8e0d0",
        directed=False,
    )
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -60,
          "centralGravity": 0.005,
          "springLength": 120,
          "springConstant": 0.08
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 150 }
      },
      "edges": {
        "color": { "color": "#B8860B44" },
        "width": 1.2,
        "smooth": { "type": "continuous" }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)

    added_hubs = set()

    def add_hub(label: str, shape: str, color: str, title: str):
        if label and label not in added_hubs:
            net.add_node(
                label,
                label=label,
                shape=shape,
                color=color,
                size=28,
                title=title,
                font={"size": 13, "color": "#e8e0d0"},
            )
            added_hubs.add(label)

    import json

    for lead in leads:
        name = lead.get("name", "Unknown")
        score = lead.get("score", 0)
        city = lead.get("city", "")
        ltype = lead.get("type", "")
        status = lead.get("status", "new")

        details = lead.get("details") or {}
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {}

        deal_type = (
            details.get("deal_type") or lead.get("deal_type") or
            details.get("acquisition_method") or lead.get("acquisition_method") or ""
        )
        owner = lead.get("owner_name") or ""

        tooltip = (
            f"<b>{name}</b><br>"
            f"Score: {score}/10<br>"
            f"Type: {ltype.replace('_',' ').title()}<br>"
            f"Deal: {deal_type}<br>"
            f"Status: {status}<br>"
            f"Owner: {owner or '—'}"
        )

        # Lead node
        net.add_node(
            name,
            label=name[:28] + ("…" if len(name) > 28 else ""),
            shape="dot",
            color=_score_color(score),
            size=_node_size(score),
            title=tooltip,
            font={"size": 11, "color": "#e8e0d0"},
        )

        # City hub
        if city:
            add_hub(city, "square", "#1565c0", f"City: {city}")
            net.add_edge(name, city)

        # Deal type hub
        if deal_type:
            add_hub(deal_type, "diamond", "#B8860B", f"Deal type: {deal_type}")
            net.add_edge(name, deal_type)

        # Owner hub (only if owner appears on multiple leads — avoids clutter)
        if owner:
            owner_leads = [l for l in leads if l.get("owner_name") == owner]
            if len(owner_leads) > 1:
                add_hub(owner, "triangle", "#9c27b0", f"Owner: {owner}")
                net.add_edge(name, owner)

    # ── Render ────────────────────────────────────────────────────────────────
    html = net.generate_html(notebook=False)
    # Force transparent background on the vis canvas
    html = html.replace(
        "body {",
        "body { background-color: #0F1B2D !important; margin: 0; "
    )
    components.html(html, height=640, scrolling=False)

    # ── Stats below graph ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    re_leads = [l for l in leads if l.get("type") == "real_estate"]
    biz_leads = [l for l in leads if l.get("type") == "business"]
    avg_score = round(sum(l.get("score", 0) for l in leads) / len(leads), 1) if leads else 0
    top_lead = max(leads, key=lambda l: l.get("score", 0))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Leads", len(leads))
    c2.metric("Real Estate", len(re_leads))
    c3.metric("Business", len(biz_leads))
    c4.metric("Avg Score", avg_score)

    st.markdown(
        f'<div class="info-box">Top lead: <strong>{top_lead.get("name")}</strong> '
        f'— Score {top_lead.get("score")}/10 · {top_lead.get("city","")}</div>',
        unsafe_allow_html=True,
    )
