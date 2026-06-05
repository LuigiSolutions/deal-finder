import streamlit as st

st.set_page_config(
    page_title="Northern Michigan Deal Finder",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Navy and Gold brand colors
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #0a1628;
        color: #e8e0d0;
    }

    section[data-testid="stSidebar"] {
        background-color: #0F1B2D;
        border-right: 1px solid #B8860B33;
    }

    section[data-testid="stSidebar"] * {
        color: #e8e0d0 !important;
    }

    .main-header {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.2rem;
        letter-spacing: 0.12em;
        background: linear-gradient(135deg, #B8860B, #FFD700, #B8860B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }

    .sub-header {
        color: #8899aa;
        font-size: 0.95rem;
        font-weight: 300;
        letter-spacing: 0.05em;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: #0F1B2D;
        border: 1px solid #B8860B44;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }

    .metric-number {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.4rem;
        color: #B8860B;
        letter-spacing: 0.05em;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #8899aa;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .badge-sent { background: #1a3a1a; color: #4caf50; border: 1px solid #4caf5044; }
    .badge-pending { background: #3a2a00; color: #FFD700; border: 1px solid #FFD70044; }
    .badge-replied { background: #1a2a3a; color: #64b5f6; border: 1px solid #64b5f644; }
    .badge-skipped { background: #2a1a1a; color: #ef5350; border: 1px solid #ef535044; }

    .stButton > button {
        background: linear-gradient(135deg, #B8860B, #8B6508);
        color: #0F1B2D;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.88rem;
        letter-spacing: 0.06em;
        padding: 0.5rem 1.2rem;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px #B8860B55;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stSelectbox"] select {
        background-color: #0F1B2D !important;
        border: 1px solid #B8860B33 !important;
        color: #e8e0d0 !important;
        border-radius: 6px !important;
    }

    .deal-row {
        background: #0F1B2D;
        border: 1px solid #B8860B22;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        transition: border-color 0.2s;
    }

    .deal-row:hover {
        border-color: #B8860B88;
    }

    .deal-name {
        font-weight: 600;
        color: #e8e0d0;
        font-size: 1rem;
    }

    .deal-meta {
        color: #8899aa;
        font-size: 0.8rem;
        margin-top: 3px;
    }

    .section-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.4rem;
        letter-spacing: 0.1em;
        color: #B8860B;
        border-bottom: 1px solid #B8860B33;
        padding-bottom: 0.4rem;
        margin-bottom: 1rem;
    }

    .info-box {
        background: #0F1B2D;
        border-left: 3px solid #B8860B;
        border-radius: 0 6px 6px 0;
        padding: 0.8rem 1rem;
        font-size: 0.88rem;
        color: #aab8c8;
        margin-bottom: 1rem;
    }

    div[data-testid="stExpander"] {
        background: #0F1B2D;
        border: 1px solid #B8860B22 !important;
        border-radius: 8px !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #8899aa;
        font-size: 0.88rem;
        letter-spacing: 0.05em;
    }

    .stTabs [aria-selected="true"] {
        color: #B8860B !important;
        border-bottom-color: #B8860B !important;
    }

    .stDataFrame {
        background: #0F1B2D;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Northern Michigan<br>Deal Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-powered acquisition lead discovery & outreach — Real Estate · Businesses</div>', unsafe_allow_html=True)

# Nav
st.sidebar.markdown("## Navigation")
page = st.sidebar.radio(
    "",
    ["📊 Dashboard", "🏠 Real Estate Agent", "🏢 Business Agent", "📬 Outreach Log", "⚙️ Settings"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size:0.78rem; color:#556677; line-height:1.6;">
<strong style="color:#B8860B;">Free Tier Stack</strong><br>
• OpenRouter (AI)<br>
• Supabase (Database)<br>
• Gmail API (Email)<br>
• Streamlit Cloud (Hosting)
</div>
""", unsafe_allow_html=True)

# Route to pages
if page == "📊 Dashboard":
    from pages import dashboard
    dashboard.render()
elif page == "🏠 Real Estate Agent":
    from pages import real_estate
    real_estate.render()
elif page == "🏢 Business Agent":
    from pages import business
    business.render()
elif page == "📬 Outreach Log":
    from pages import outreach_log
    outreach_log.render()
elif page == "⚙️ Settings":
    from pages import settings
    settings.render()
