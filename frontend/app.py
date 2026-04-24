import html
import requests
import streamlit as st


# Backend URLs
RAILWAY_URL = "https://bidgenius-production.up.railway.app/api"
VERCEL_URL = "https://bidgen-api.vercel.app/api"

if "backend_url" not in st.session_state:
    st.session_state.backend_url = RAILWAY_URL

COMPANY_TYPES = [
    "Construction / Civil",
    "IT Services",
    "Electrical / MEP",
    "Environmental / Water",
    "Consulting / Advisory",
    "Supply / Procurement",
    "Other",
]
SCOPE_OPTIONS = {
    "all": "All portals",
    "central": "Central Govt (GEM, eProcure)",
    "state": "State Govt portals",
    "municipal": "Municipal Corporations",
    "psu": "PSUs (Railways, NHAI, NTPC)",
}


st.set_page_config(
    page_title="BidGenius AI",
    layout="wide",
    page_icon="📑",
    initial_sidebar_state="expanded",
)

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.title("Settings")
    
    # Backend Selector
    backend_mode = st.radio(
        "Backend Engine",
        ["Railway (Primary - Unlimited)", "Vercel (Backup - 10s Limit)"],
        index=0,
        help="Use Railway for Full Analysis. Vercel is good for quick lists."
    )
    
    if "Railway" in backend_mode:
        st.session_state.backend_url = RAILWAY_URL
    else:
        st.session_state.backend_url = VERCEL_URL

    st.divider()



def escape_text(value, fallback="—"):
    if value is None:
        return fallback
    text = str(value).strip()
    return html.escape(text) if text else fallback


def truncate_text(value, limit, fallback="—"):
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    return html.escape(text[:limit] + ("..." if len(text) > limit else ""))


def normalize_score(value):
    try:
        return min(max(int(float(value)), 0), 100)
    except (TypeError, ValueError):
        return 0


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #08111f;
            --panel: rgba(10, 18, 33, 0.78);
            --panel-strong: rgba(13, 23, 42, 0.92);
            --panel-soft: rgba(255, 255, 255, 0.05);
            --border: rgba(162, 197, 255, 0.18);
            --text: #f5f7fb;
            --muted: #9eb0cb;
            --accent: #5de4c7;
            --accent-strong: #28c4ff;
            --accent-warm: #ffb86b;
            --danger: #ff8f8f;
            --shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
        }

        html, body, [class*="css"] {
            font-family: "Manrope", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(40, 196, 255, 0.20), transparent 28%),
                radial-gradient(circle at top right, rgba(93, 228, 199, 0.16), transparent 26%),
                radial-gradient(circle at 20% 80%, rgba(255, 184, 107, 0.14), transparent 22%),
                linear-gradient(180deg, #06101d 0%, #08111f 48%, #050b14 100%);
            color: var(--text);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(8, 17, 31, 0.96), rgba(11, 20, 36, 0.92));
            border-right: 1px solid rgba(162, 197, 255, 0.14);
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        /* --- INPUT TEXT COLOR FIX --- */
        /* Forces the text you type into inputs and textareas to be black */
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stNumberInput input {
            color: #000000 !important;
            background: #ffffff !important;
        }
        
        /* Ensures selectbox text is also legible */
        .stSelectbox [data-baseweb="select"] > div {
            color: #000000 !important;
            background: #ffffff !important;
        }
        /* --------------------------- */

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        h1, h2, h3, h4 {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.03em;
            color: var(--text);
        }

        p, li, div[data-testid="stMarkdownContainer"] p {
            color: rgba(245, 247, 251, 0.92);
        }

        .glass-shell {
            background: linear-gradient(180deg, rgba(15, 25, 44, 0.88), rgba(10, 19, 35, 0.72));
            border: 1px solid var(--border);
            border-radius: 28px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
        }

        .hero-shell {
            padding: 2rem;
            margin-bottom: 1.35rem;
            overflow: hidden;
            position: relative;
        }

        .hero-shell::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(135deg, rgba(40, 196, 255, 0.16), transparent 42%),
                radial-gradient(circle at 85% 18%, rgba(93, 228, 199, 0.18), transparent 16%);
            pointer-events: none;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.6fr) minmax(310px, 0.9fr);
            gap: 1.4rem;
            align-items: stretch;
            position: relative;
            z-index: 1;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.9rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--accent);
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }

        .hero-title {
            margin: 1rem 0 0.8rem;
            font-size: clamp(2.5rem, 5vw, 4.3rem);
            line-height: 0.96;
            max-width: 11ch;
        }

        .hero-copy {
            max-width: 62ch;
            color: var(--muted);
            font-size: 1.02rem;
            line-height: 1.75;
            margin-bottom: 1.2rem;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
        }

        .hero-chip {
            padding: 0.7rem 0.95rem;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #d7e3f6;
            font-size: 0.92rem;
        }

        .hero-panel {
            padding: 1.4rem;
            border-radius: 24px;
            background:
                linear-gradient(160deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03));
            border: 1px solid rgba(255, 255, 255, 0.08);
            min-height: 100%;
        }

        .panel-kicker {
            color: var(--accent-warm);
            text-transform: uppercase;
            font-size: 0.72rem;
            letter-spacing: 0.14em;
            font-weight: 800;
        }

        .panel-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.25rem;
            margin: 0.6rem 0 1.1rem;
            color: var(--text);
        }

        .snapshot-card {
            padding: 0.9rem 1rem;
            border-radius: 18px;
            background: rgba(5, 11, 20, 0.44);
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 0.75rem;
        }

        .snapshot-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.32rem;
        }

        .snapshot-value {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text);
        }

        .section-lead {
            margin: 0.8rem 0 1.1rem;
            color: var(--muted);
        }

        .workflow-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin: 0.5rem 0 1.5rem;
        }

        .workflow-card {
            padding: 1.15rem;
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.08);
            min-height: 176px;
        }

        .workflow-index {
            width: 40px;
            height: 40px;
            border-radius: 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(40, 196, 255, 0.26), rgba(93, 228, 199, 0.18));
            border: 1px solid rgba(93, 228, 199, 0.24);
            color: var(--text);
            font-weight: 800;
            margin-bottom: 1rem;
        }

        .workflow-card h4 {
            margin: 0 0 0.45rem;
            font-size: 1.05rem;
        }

        .workflow-card p {
            margin: 0;
            color: var(--muted);
            line-height: 1.7;
        }

        .search-shell {
            padding: 1.25rem;
            margin: 0.35rem 0 1.2rem;
        }

        .search-shell h3 {
            margin: 0 0 0.35rem;
            font-size: 1.28rem;
        }

        .search-shell p {
            color: var(--muted);
            margin-bottom: 1rem;
        }

        .sidebar-banner,
        .inline-note {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--muted);
        }

        .sidebar-banner strong,
        .inline-note strong {
            color: var(--text);
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(13, 23, 42, 0.82), rgba(10, 18, 33, 0.74));
            border: 1px solid rgba(162, 197, 255, 0.14);
            border-radius: 22px;
            padding: 1rem 1rem 0.9rem 1rem;
            box-shadow: 0 16px 32px rgba(0, 0, 0, 0.18);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
            font-family: "Space Grotesk", sans-serif;
            font-weight: 700;
            letter-spacing: -0.03em;
        }

        .summary-strip {
            padding: 1rem 1.2rem;
            margin: 1rem 0 1.25rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(40, 196, 255, 0.12), rgba(93, 228, 199, 0.06));
            border: 1px solid rgba(93, 228, 199, 0.16);
        }

        .summary-strip strong {
            color: var(--text);
        }

        .result-shell {
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-radius: 26px;
            background: linear-gradient(180deg, rgba(13, 23, 42, 0.86), rgba(9, 16, 29, 0.72));
            border: 1px solid rgba(162, 197, 255, 0.14);
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.22);
        }

        .result-topline {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 1rem;
            align-items: flex-start;
            margin-bottom: 0.8rem;
        }

        .result-title {
            margin: 0.28rem 0 0.45rem;
            font-size: 1.4rem;
            max-width: 18ch;
        }

        .result-meta {
            color: var(--muted);
            line-height: 1.65;
            margin: 0;
        }

        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.45rem;
        }

        .badge {
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            border: 1px solid transparent;
        }

        .badge-active {
            background: rgba(93, 228, 199, 0.12);
            color: #8af6df;
            border-color: rgba(93, 228, 199, 0.22);
        }

        .badge-unknown {
            background: rgba(255, 184, 107, 0.12);
            color: #ffd39f;
            border-color: rgba(255, 184, 107, 0.22);
        }

        .badge-expired {
            background: rgba(255, 143, 143, 0.12);
            color: #ffc0c0;
            border-color: rgba(255, 143, 143, 0.22);
        }

        .badge-corr {
            background: rgba(40, 196, 255, 0.12);
            color: #92e4ff;
            border-color: rgba(40, 196, 255, 0.22);
        }

        .score-badge {
            min-width: 132px;
            padding: 0.95rem 1rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.08);
            text-align: center;
        }

        .score-label {
            color: var(--muted);
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.3rem;
        }

        .score-value {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--text);
            line-height: 1;
        }

        .score-sub {
            margin-top: 0.3rem;
            color: var(--muted);
            font-size: 0.82rem;
        }

        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem 1rem;
        }

        .detail-card {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.07);
        }

        .detail-label {
            font-size: 0.76rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 0.34rem;
        }

        .detail-value {
            color: var(--text);
            font-weight: 700;
            line-height: 1.5;
            word-break: break-word;
        }

        .quick-card {
            padding: 1.05rem 1.15rem;
            margin-bottom: 0.8rem;
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }

        .quick-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            margin-bottom: 0.6rem;
            padding: 0.38rem 0.75rem;
            border-radius: 999px;
            background: rgba(40, 196, 255, 0.12);
            border: 1px solid rgba(40, 196, 255, 0.16);
            color: #9be9ff;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .flag-note {
            padding: 0.82rem 0.95rem;
            border-radius: 16px;
            background: rgba(255, 184, 107, 0.10);
            border: 1px solid rgba(255, 184, 107, 0.16);
            color: #ffe0ba;
            margin-bottom: 0.6rem;
        }

        .fee-note {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(40, 196, 255, 0.12), rgba(93, 228, 199, 0.08));
            border: 1px solid rgba(93, 228, 199, 0.16);
            color: #d9f7ef;
            margin: 0.8rem 0 1rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.65rem;
            margin-bottom: 0.7rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            padding: 0.5rem 1rem;
            color: var(--muted);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(40, 196, 255, 0.22), rgba(93, 228, 199, 0.16));
            color: var(--text);
            border-color: rgba(93, 228, 199, 0.2);
        }

        .stAlert {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
        }

        .stRadio > div {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 0.5rem 0.7rem;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stLinkButton > a {
            background: linear-gradient(135deg, #28c4ff 0%, #5de4c7 100%);
            color: #07131d !important;
            border: none;
            border-radius: 16px;
            font-weight: 800;
            box-shadow: 0 14px 24px rgba(27, 121, 167, 0.28);
            min-height: 3rem;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stLinkButton > a:hover {
            filter: brightness(1.03);
            transform: translateY(-1px);
        }

        .stProgress > div > div > div > div {
            background: linear-gradient(135deg, #28c4ff 0%, #5de4c7 100%);
        }

        a {
            color: #92e4ff !important;
        }

        @media (max-width: 1100px) {
            .hero-grid,
            .workflow-grid,
            .detail-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(mode, scope):
    mode_copy = (
        "Deep extraction, compliance scoring, and draft generation"
        if mode == "Full analysis"
        else "Fast scan mode for instant opportunity discovery"
    )
    scope_copy = SCOPE_OPTIONS.get(scope, "All portals")
    st.markdown(
        f"""
        <div class="glass-shell hero-shell">
            <div class="hero-grid">
                <div>
                    <div class="eyebrow">Agentic Tender Intelligence</div>
                    <h1 class="hero-title">Search faster. Qualify better. Draft smarter.</h1>
                    <p class="hero-copy">
                        An operator-grade workspace for government tender discovery, document analysis,
                        bid-fit scoring, and proposal drafting. Built to feel closer to a deal desk than a basic search page.
                    </p>
                    <div class="chip-row">
                        <div class="hero-chip">Tender discovery across public procurement sources</div>
                        <div class="hero-chip">Opportunity scoring with active-status checks</div>
                        <div class="hero-chip">Bid proposal generation from your company profile</div>
                    </div>
                </div>
                <div class="hero-panel">
                    <div class="panel-kicker">Current Search Posture</div>
                    <div class="panel-title">Configured for execution</div>
                    <div class="snapshot-card">
                        <div class="snapshot-label">Mode</div>
                        <div class="snapshot-value">{escape_text(mode)}</div>
                    </div>
                    <div class="snapshot-card">
                        <div class="snapshot-label">Portal Scope</div>
                        <div class="snapshot-value">{escape_text(scope_copy)}</div>
                    </div>
                    <div class="snapshot-card">
                        <div class="snapshot-label">Pipeline</div>
                        <div class="snapshot-value">{escape_text(mode_copy)}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow():
    st.markdown(
        """
        <p class="section-lead">
            The interface is tuned for procurement teams that need a fast signal on whether a tender is worth pursuing,
            what the commercial thresholds look like, and how quickly a draft response can be prepared.
        </p>
        <div class="workflow-grid">
            <div class="workflow-card">
                <div class="workflow-index">01</div>
                <h4>Search with intent</h4>
                <p>Use keyword, region, and scope filters to cut through noisy portals and focus on relevant opportunities.</p>
            </div>
            <div class="workflow-card">
                <div class="workflow-index">02</div>
                <h4>Read the signal</h4>
                <p>Review fees, EMD, estimated value, deadlines, and bid-fit scoring in a structured analysis surface.</p>
            </div>
            <div class="workflow-card">
                <div class="workflow-index">03</div>
                <h4>Move to proposal</h4>
                <p>Generate a first-pass bid draft grounded in your company profile so the response team starts ahead.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_header(title, status_class, status_label, score, difficulty, category, is_corrigendum):
    normalized_score = normalize_score(score)
    corrigendum_badge = (
        '<span class="badge badge-corr">Corrigendum</span>' if is_corrigendum else ""
    )
    category_text = escape_text(category, "General")
    st.markdown(
        f"""
        <div class="result-shell">
            <div class="result-topline">
                <div>
                    <div class="badge-row">
                        <span class="badge {status_class}">{escape_text(status_label)}</span>
                        {corrigendum_badge}
                    </div>
                    <h3 class="result-title">{escape_text(title, "Untitled tender")}</h3>
                    <p class="result-meta">
                        Difficulty: <strong>{escape_text(difficulty, "—")}</strong>
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        Category: <strong>{category_text}</strong>
                    </p>
                </div>
                <div class="score-badge">
                    <div class="score-label">Bid Fit Score</div>
                    <div class="score-value">{normalized_score}/100</div>
                    <div class="score-sub">Prioritise higher scores first</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_detail_cards(rows):
    cards = []
    for label, value in rows.items():
        cards.append(
            f"""
            <div class="detail-card">
                <div class="detail-label">{escape_text(label)}</div>
                <div class="detail-value">{escape_text(value)}</div>
            </div>
            """
        )
    st.markdown(f'<div class="detail-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def compute_summary_stats(items):
    scores = []
    active_count = 0
    with_bid_count = 0

    for item in items:
        analysis = item.get("analysis", {})
        bid = item.get("bid", {})
        score = analysis.get("score")
        if isinstance(score, (int, float)):
            scores.append(score)
        if analysis.get("is_active") is True:
            active_count += 1
        if bid.get("proposal"):
            with_bid_count += 1

    average_score = round(sum(scores) / len(scores), 1) if scores else 0
    return active_count, average_score, with_bid_count


inject_styles()

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-banner">
            <strong>BidGenius AI</strong><br/>
            Set your company profile once, then run either a fast opportunity scan or a full tender analysis workflow.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Company Context")
    st.caption("Used to personalize bid proposals and eligibility narrative.")

    company_name = st.text_input(
        "Company name *",
        placeholder="e.g. Infra Solutions Pvt. Ltd.",
        help="Your registered company name",
    )
    company_type = st.selectbox("Company type", COMPANY_TYPES)
    turnover_cr = st.number_input(
        "Annual turnover (INR crore)",
        min_value=0.0,
        max_value=10000.0,
        value=5.0,
        step=0.5,
        help="Used in compliance and capability positioning.",
    )
    experience_yrs = st.number_input(
        "Years in business",
        min_value=1,
        max_value=100,
        value=5,
    )
    certifications = st.text_input(
        "Key certifications",
        placeholder="ISO 9001, MSME, GST registered",
    )
    past_projects = st.text_area(
        "Notable past projects",
        placeholder="Roadworks, solar EPC, CCTV rollout, IT modernization programs",
        height=90,
    )

    st.divider()
    st.markdown("### Search Controls")
    scope = st.selectbox(
        "Portal scope",
        list(SCOPE_OPTIONS),
        format_func=lambda x: SCOPE_OPTIONS[x],
    )
    mode = st.radio("Mode", ["Full analysis", "Quick list"], horizontal=True)
    st.markdown(
        f"""
        <div class="inline-note">
            <strong>{escape_text(mode)}</strong><br/>
            {"Downloads documents, extracts fields, scores the tender, and drafts a proposal." if mode == "Full analysis" else "Returns a fast list of relevant opportunities for early screening."}
        </div>
        """,
        unsafe_allow_html=True,
    )


render_hero(mode, scope)
render_workflow()

st.markdown(
    """
    <div class="glass-shell search-shell">
        <h3>Search Workspace</h3>
        <p>Enter a market keyword and geographic focus, then launch the pipeline that fits your urgency.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("tender_search_form", clear_on_submit=False):
    col_kw, col_reg, col_btn = st.columns([3.3, 2.1, 1.1])
    with col_kw:
        keyword = st.text_input(
            "Tender keyword",
            placeholder="road construction, CCTV, smart meters, cloud migration, water treatment",
        )
    with col_reg:
        region = st.text_input(
            "Region / city",
            value="India",
            placeholder="Maharashtra, Mumbai, Delhi",
        )
    with col_btn:
        st.write("")
        st.write("")
        run = st.form_submit_button("Launch Search", use_container_width=True, type="primary")

if run and mode == "Full analysis" and not company_name.strip():
    st.warning("Add your company name in the sidebar to generate a personalized bid proposal.")

if run and not keyword.strip():
    st.warning("Enter a keyword before launching the search.")

if run and keyword.strip():
    status = st.empty()

    if mode == "Quick list":
        status.info(f"Finding tender leads for '{keyword}' in '{region}'...")
        try:
            response = requests.post(
                f"{st.session_state.backend_url}/list",
                json={"keyword": keyword, "region": region},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
        except requests.ConnectionError:
            status.error("Cannot connect to the backend on port 8000. Start the API service first.")
            st.stop()
        except Exception as exc:
            status.error(f"Search failed: {exc}")
            st.stop()

        status.empty()

        if not data:
            st.warning("No results found. Try a broader keyword, a larger region, or switch scope.")
            st.stop()

        st.markdown(
            f"""
            <div class="summary-strip">
                <strong>{len(data)} opportunities</strong> surfaced for <strong>{escape_text(keyword)}</strong> in
                <strong>{escape_text(region)}</strong>. Use this as a shortlist before running full analysis.
            </div>
            """,
            unsafe_allow_html=True,
        )

        for item in data:
            icon_label = "PDF Source" if item.get("is_pdf") else "Web Source"
            st.markdown(
                f"""
                <div class="quick-card">
                        <div class="quick-tag">{escape_text(icon_label)}</div>
                        <h4 style="margin:0 0 0.5rem 0;">{escape_text(item.get('title'), 'Untitled result')}</h4>
                        <p style="margin:0; color: var(--muted); line-height:1.7;">
                        {truncate_text(item.get('snippet'), 420, 'No preview available.')}
                        </p>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            if item.get("url"):
                st.markdown(f"[Open source]({item['url']})")

    else:
        profile = {
            "company_name": company_name.strip() or "Our Company",
            "company_type": company_type,
            "turnover_cr": turnover_cr,
            "experience_yrs": experience_yrs,
            "certifications": certifications.strip(),
            "past_projects": past_projects.strip(),
        }

        status.info(
            "Running full tender analysis. Downloading source files, extracting structured fields, "
            "and generating bid content. This can take 3 to 5 minutes."
        )

        try:
            response = requests.post(
                f"{st.session_state.backend_url}/run",
                json={
                    "keyword": keyword,
                    "region": region,
                    "scope": scope,
                    "profile": profile,
                },
                timeout=360,
            )
            if not response.ok:
                try:
                    error_payload = response.json()
                    status.error(
                        f"Backend error ({response.status_code}): {error_payload.get('error', response.text)}"
                    )
                except Exception:
                    status.error(f"Backend error ({response.status_code}): {response.text[:500]}")
                st.stop()

            data = response.json()
        except requests.Timeout:
            status.error("The request timed out after 6 minutes. Try Quick list mode or narrow the keyword.")
            st.stop()
        except requests.ConnectionError:
            status.error("Cannot connect to the backend on port 8000. Start the API service first.")
            st.stop()
        except Exception as exc:
            status.error(f"Analysis failed: {exc}")
            st.stop()

        status.empty()

        if not data:
            st.warning(
                "No active relevant tenders were found. Try Quick list mode, broaden the keyword, "
                "or switch the portal scope."
            )
            st.stop()

        active_count, average_score, with_bid_count = compute_summary_stats(data)

        st.markdown(
            f"""
            <div class="summary-strip">
                Full analysis completed for <strong>{escape_text(keyword)}</strong> in <strong>{escape_text(region)}</strong>.
                Review the shortlist below and prioritize high-score active tenders.
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_1, metric_2, metric_3, metric_4 = st.columns(4)
        metric_1.metric("Tenders found", len(data))
        metric_2.metric("Active tenders", active_count)
        metric_3.metric("Average score", f"{average_score}/100")
        metric_4.metric("Drafts generated", with_bid_count)

        for index, item in enumerate(data):
            tender = item.get("tender", {})
            raw = item.get("raw_data", {})
            ui = item.get("ui_data", {})
            analysis = item.get("analysis", {})
            bid = item.get("bid", {})

            is_active = analysis.get("is_active")
            if is_active is True:
                status_class = "badge-active"
                status_label = "Active"
            elif is_active is False:
                status_class = "badge-expired"
                status_label = "Expired"
            else:
                status_class = "badge-unknown"
                status_label = "Status Unknown"

            score = normalize_score(analysis.get("score", 0))
            render_result_header(
                title=tender.get("title", "Untitled tender"),
                status_class=status_class,
                status_label=status_label,
                score=score,
                difficulty=analysis.get("difficulty", "—"),
                category=raw.get("primary_category", "General"),
                is_corrigendum=raw.get("is_corrigendum"),
            )

            metric_a, metric_b, metric_c, metric_d = st.columns(4)
            metric_a.metric("Tender fee", ui.get("Tender Fee", "—"))
            metric_b.metric("EMD / Security", ui.get("EMD", "—"))
            metric_c.metric("Estimated value", ui.get("Estimated Cost", "—"))
            metric_d.metric("Bid deadline", ui.get("Bid End Date", "—"))

            st.progress(score / 100, text=f"Bid fit score: {score}/100")

            tender_fee = raw.get("Tender Fee")
            emd = raw.get("EMD")
            if tender_fee and emd:
                st.markdown(
                    f"""
                    <div class="fee-note">
                        Upfront document fee: <strong>{escape_text(ui.get("Tender Fee"))}</strong>
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        Refundable bid security: <strong>{escape_text(ui.get("EMD"))}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif emd:
                st.markdown(
                    f"""
                    <div class="fee-note">
                        Refundable bid security required: <strong>{escape_text(ui.get("EMD"))}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            summary_tab, details_tab, proposal_tab = st.tabs(["Executive summary", "Tender details", "Bid proposal"])

            with summary_tab:
                st.markdown(analysis.get("summary") or "No summary extracted. Open the original source document.")
                flags = analysis.get("flags") or []
                if flags:
                    st.markdown("##### Risk signals")
                    for flag in flags:
                        st.markdown(
                            f'<div class="flag-note">{escape_text(flag)}</div>',
                            unsafe_allow_html=True,
                        )

            with details_tab:
                detail_rows = {
                    "Tender ID": raw.get("Tender ID"),
                    "Organization": ui.get("Organization"),
                    "Ministry": ui.get("Ministry"),
                    "Location": ui.get("Location"),
                    "Publish date": ui.get("Publish Date"),
                    "Bid start date": ui.get("Bid Start Date"),
                    "Bid end date": ui.get("Bid End Date"),
                    "Bid opening date": ui.get("Bid Opening Date"),
                    "Tender fee": ui.get("Tender Fee"),
                    "EMD / Security": ui.get("EMD"),
                    "Estimated contract value": ui.get("Estimated Cost"),
                    "Turnover required": ui.get("Turnover"),
                    "Category": raw.get("primary_category"),
                    "Corrigendum / amendment": "Yes" if raw.get("is_corrigendum") else "No",
                }
                render_detail_cards(detail_rows)
                if tender.get("url"):
                    st.markdown(f"[Open original source]({tender['url']})")

            with proposal_tab:
                proposal = bid.get("proposal", "")
                if proposal:
                    st.markdown(proposal)
                    st.download_button(
                        label="Download proposal (.txt)",
                        data=proposal,
                        file_name=f"bid_{index + 1}_{keyword.replace(' ', '_')}.txt",
                        mime="text/plain",
                        key=f"download_{index}",
                    )
                else:
                    st.info("A proposal draft was not generated for this tender. Use the source file for manual drafting.")