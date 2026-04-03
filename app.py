"""
Rome Flip Analyzer — Hoofdapplicatie
Vastgoedanalyse-tool voor buy-renovate-sell investeringen in Rome.
"""
from __future__ import annotations

import streamlit as st

from config import DEFAULT_PARAMS
from models.financial import calculate_investment_analysis
from models.scoring import calculate_flip_score
from models.comparables import (
    calculate_relative_position,
    estimate_selling_speed,
    calculate_confidence_level,
)
from services.feature_extractor import extract_property_features
from components.dashboard import render_dashboard
from components.property_detail import render_property_detail
from components.settings_panel import render_settings
from components.search_panel import render_search_panel, render_filters
from components.neighborhood_view import render_neighborhood_view
from components.auth_page import render_auth_page
from components.search_history import render_search_history
from components.favorites import render_favorites
from services.pdf_export import generate_batch_report
from services.auth import is_logged_in, get_current_user, logout, restore_session
from services.database import save_search


# === PAGINA CONFIGURATIE ===
st.set_page_config(
    page_title="Rome Flip Analyzer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === DYNAMIC THEME CSS ===
def _inject_theme_css():
    """Injecteert premium CSS op basis van het huidige thema (light/dark)."""
    dark = st.session_state.get("dark_mode", False)

    # Font laden via <link> tag (niet @import, dat breekt in Streamlit)
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )

    common = """
    /* === GLOBAL === */
    .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important; }
    .stApp > header { background-color: transparent !important; }
    #MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }
    h1, h2, h3, h4, h5 { font-family: 'Inter', sans-serif !important; letter-spacing: -0.02em !important; }
    .stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th,
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        font-family: 'Inter', sans-serif !important;
    }
    .main .block-container { max-width: 1400px !important; }

    /* === SIDEBAR — licht thema === */
    section[data-testid="stSidebar"] {
        background: #F3F0EC !important;
        border-right: 1px solid rgba(0,0,0,0.06) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stCaption p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #1A1A2E !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1A1A2E !important;
    }
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stNumberInput input,
    section[data-testid="stSidebar"] .stTextArea textarea,
    section[data-testid="stSidebar"] input {
        background: #FFFFFF !important;
        border: 1.5px solid rgba(0,0,0,0.12) !important;
        border-radius: 12px !important;
        color: #1A1A2E !important;
        -webkit-text-fill-color: #1A1A2E !important;
    }
    section[data-testid="stSidebar"] input::placeholder {
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border: 1.5px solid rgba(0,0,0,0.12) !important;
        border-radius: 12px !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] span { color: #1A1A2E !important; }
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #E8956A, #D4764A) !important;
        color: white !important; border: none !important;
        border-radius: 12px !important; font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(232,149,106,0.3) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stDownloadButton"] button {
        background: #FFFFFF !important;
        color: #1A1A2E !important; border: 1.5px solid rgba(0,0,0,0.12) !important;
    }

    /* === BUTTONS === */
    .stButton > button, button[kind="primary"] {
        background: linear-gradient(135deg, #E8956A, #D4764A) !important;
        color: white !important; border: none !important;
        border-radius: 12px !important; font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 4px 12px rgba(232,149,106,0.25) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover, button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(232,149,106,0.4) !important;
        transform: translateY(-1px);
    }
    button[kind="secondary"] {
        background: transparent !important;
        border: 1.5px solid rgba(0,0,0,0.1) !important;
        border-radius: 12px !important; font-weight: 500 !important;
        box-shadow: none !important; color: #1A1A2E !important;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 2px solid rgba(0,0,0,0.04); }
    .stTabs [data-baseweb="tab"] {
        border: none !important; border-radius: 10px 10px 0 0 !important;
        padding: 10px 24px !important; font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important; font-size: 0.9rem !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #E8956A !important; }

    /* === SLIDERS === */
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        background-color: #E8956A !important;
    }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.18); }

    /* === DIVIDER === */
    hr, [data-testid="stSeparator"] { border-color: rgba(0,0,0,0.06) !important; }
    """

    if dark:
        theme = """
        /* ===== DARK MODE ===== */
        .stApp { background-color: #0F0F1A !important; }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 { color: #F1F5F9 !important; }
        .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th,
        .stMarkdown strong, .stMarkdown em, .stMarkdown span { color: #E2E8F0 !important; }
        .stCaption, [data-testid="stCaptionContainer"] p { color: #94A3B8 !important; }

        div[data-testid="stMetric"] {
            background-color: #1A1A2E !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 16px; padding: 16px 20px;
        }
        div[data-testid="stMetric"] label { color: #94A3B8 !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #F1F5F9 !important; font-weight: 700 !important; }

        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            background-color: #1A1A2E !important; color: #E2E8F0 !important;
            border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 12px !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: #E8956A !important;
            box-shadow: 0 0 0 3px rgba(232,149,106,0.15) !important;
        }
        .stTextInput label, .stNumberInput label, .stTextArea label,
        .stSelectbox label, .stSlider label, .stCheckbox label { color: #E2E8F0 !important; }
        [data-baseweb="select"] > div { background-color: #1A1A2E !important; border-radius: 12px !important; }
        [data-baseweb="select"] span { color: #E2E8F0 !important; }
        [data-baseweb="popover"] > div { background-color: #1A1A2E !important; }
        [data-baseweb="menu"] { background-color: #1A1A2E !important; }
        [data-baseweb="menu"] li { color: #E2E8F0 !important; }
        [data-baseweb="menu"] li:hover { background-color: #252540 !important; }

        [data-testid="stExpander"] { border-color: rgba(255,255,255,0.06) !important; }
        [data-testid="stExpander"] summary { color: #E2E8F0 !important; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(255,255,255,0.06) !important; background-color: #0F0F1A !important;
        }
        button[kind="secondary"] {
            background-color: #1A1A2E !important; color: #E2E8F0 !important;
            border-color: rgba(255,255,255,0.1) !important;
        }
        .stTabs [data-baseweb="tab"] { color: #94A3B8 !important; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #F1F5F9 !important; }
        .stTabs [data-baseweb="tab-border"] { background-color: rgba(255,255,255,0.04) !important; }
        .stMarkdown table { border-color: rgba(255,255,255,0.06) !important; }
        .stMarkdown table th { background-color: #1A1A2E !important; color: #F1F5F9 !important; border-color: rgba(255,255,255,0.06) !important; }
        .stMarkdown table td { color: #E2E8F0 !important; border-color: rgba(255,255,255,0.04) !important; }
        [data-testid="stAlert"] > div { background-color: #1A1A2E !important; color: #E2E8F0 !important; }
        hr, [data-testid="stSeparator"] { border-color: rgba(255,255,255,0.04) !important; }
        a { color: #E8956A !important; }
        [data-testid="stDownloadButton"] button {
            background-color: #1A1A2E !important; color: #E2E8F0 !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
        }
        [data-testid="stForm"] { border-color: rgba(255,255,255,0.06) !important; }
        .stApp [style*="color:#64748B"] { color: #94A3B8 !important; }
        .stApp [style*="color:#94A3B8"] { color: #475569 !important; }
        .stApp [style*="color:#1A1A2E"] { color: #E2E8F0 !important; }
        .stApp [style*="background:#F3F0EC"] { background-color: #1A1A2E !important; }
        [data-testid="stSpinner"] p { color: #94A3B8 !important; }
        section[data-testid="stSidebar"] {
            background: #1A1A2E !important;
        }
        """
    else:
        theme = """
        /* ===== LIGHT MODE ===== */
        .stApp { background-color: #FAF8F5 !important; }

        div[data-testid="stMetric"] {
            background: #FFFFFF; border: 1px solid rgba(0,0,0,0.04);
            border-radius: 16px; padding: 18px 22px;
            box-shadow: 0 2px 16px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetric"] label {
            font-weight: 500 !important; font-size: 0.7rem !important;
            text-transform: uppercase !important; letter-spacing: 0.06em !important;
            color: #94A3B8 !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-weight: 700 !important; color: #1A1A2E !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(0,0,0,0.04) !important; background-color: #FFFFFF !important;
            border-radius: 16px !important; box-shadow: 0 2px 16px rgba(0,0,0,0.05);
        }
        .stTextInput input, .stNumberInput input {
            background: #FFFFFF !important; border: 1.5px solid rgba(0,0,0,0.08) !important;
            border-radius: 12px !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: #E8956A !important;
            box-shadow: 0 0 0 3px rgba(232,149,106,0.12) !important;
        }
        [data-testid="stExpander"] summary { font-weight: 600 !important; }
        .stTabs [data-baseweb="tab"] { color: #94A3B8 !important; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #1A1A2E !important; font-weight: 600 !important; }
        """

    st.markdown(f"<style>{common}{theme}</style>", unsafe_allow_html=True)


_inject_theme_css()


def init_session_state():
    """Initialiseer session state variabelen."""
    if "params" not in st.session_state:
        st.session_state["params"] = DEFAULT_PARAMS.copy()
    if "raw_listings" not in st.session_state:
        st.session_state["raw_listings"] = []
    if "analyzed_listings" not in st.session_state:
        st.session_state["analyzed_listings"] = []
    if "selected_property_idx" not in st.session_state:
        st.session_state["selected_property_idx"] = None
    if "active_tab" not in st.session_state:
        st.session_state["active_tab"] = "Dashboard"
    if "export_pdf" not in st.session_state:
        st.session_state["export_pdf"] = False
    if "property_overrides" not in st.session_state:
        st.session_state["property_overrides"] = {}
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False


def analyze_listings(listings: list[dict], params: dict) -> list[dict]:
    """
    Draait de volledige analyse op alle listings:
    feature extractie + financieel model + scoring + comparables.
    """
    analyzed = []
    for listing in listings:
        # 1. Extract NLP features (terras, lift, vincolo, etc.)
        if not listing.get("features"):
            listing["features"] = extract_property_features(listing)

        # 2. Financiële analyse (inclusief locatie + verkoopprijsschatting)
        analysis = calculate_investment_analysis(listing, params)

        # 3. Flip Score
        score_data = calculate_flip_score(listing, analysis, params)

        # Voeg analyse-resultaten toe aan listing
        enriched = listing.copy()
        enriched["analysis"] = analysis
        enriched["score_data"] = score_data
        enriched["flip_score"] = score_data["flip_score"]
        enriched["midpoint_roi"] = analysis["midpoint_roi"]
        enriched["risk_flags"] = score_data["risk_flags"]
        enriched["location_quality"] = analysis.get("location_quality", {})
        enriched["sale_price_estimate"] = analysis.get("sale_price_estimate", {})

        # Prima casa als hoofdscenario
        prima = analysis["prima_casa"]
        seconda = analysis["seconda_casa"]
        enriched["roi_prima_casa"] = prima["roi"]
        enriched["roi_seconda_casa"] = seconda["roi"]
        enriched["net_profit_prima"] = prima["net_profit"]
        enriched["net_profit_seconda"] = seconda["net_profit"]
        enriched["estimated_renovation_cost"] = prima["renovation"]
        enriched["estimated_sale_price"] = prima["sale_price"]
        enriched["total_investment"] = prima["total_investment"]

        # Backward compat
        enriched["roi_conservative"] = seconda["roi"]
        enriched["roi_optimistic"] = prima["roi"]
        enriched["net_profit_conservative"] = seconda["net_profit"]
        enriched["net_profit_optimistic"] = prima["net_profit"]

        analyzed.append(enriched)

    # Sorteer op flip score (aflopend)
    analyzed.sort(key=lambda x: x["flip_score"], reverse=True)

    # 4. Post-sort: batch comparables, selling speed, confidence
    for enriched in analyzed:
        comparables = calculate_relative_position(enriched, analyzed)
        enriched["comparables"] = comparables

        selling_speed = estimate_selling_speed(enriched, enriched["analysis"], comparables)
        enriched["selling_speed"] = selling_speed

        confidence = calculate_confidence_level(comparables)
        enriched["confidence"] = confidence

    return analyzed


def _has_supabase_config() -> bool:
    """Controleert of Supabase credentials geconfigureerd zijn."""
    try:
        return bool(st.secrets.get("supabase", {}).get("url"))
    except (AttributeError, FileNotFoundError):
        return False


def _handle_direct_detail_link() -> bool:
    """
    Handle direct link to property detail (opened in a new browser tab).
    URL format: ?sid=<search_id>&url=<encoded_listing_url>
    Returns True if handled (caller should return early).
    """
    from urllib.parse import unquote

    qp = st.query_params
    sid = qp.get("sid")
    target_url = qp.get("url")
    if not sid or not target_url:
        return False

    target_url = unquote(target_url)

    try:
        from services.database import get_saved_listings
        listings = get_saved_listings(sid)
    except Exception:
        listings = []

    if not listings:
        st.error("Zoekresultaten niet gevonden of verlopen.")
        return True

    listing = next((l for l in listings if l.get("url") == target_url), None)
    if not listing:
        st.error("Pand niet gevonden in de zoekresultaten.")
        return True

    analysis = listing.get("analysis", {})
    score_data = listing.get("score_data", {})
    params = DEFAULT_PARAMS.copy()

    # Dark mode toggle voor direct-link pagina
    dm_col1, dm_col2 = st.columns([4, 1])
    with dm_col1:
        st.markdown(
            "<h2 style='color: #1A1A2E; margin-bottom: 0; font-family: Inter, sans-serif;'>"
            "🏛️ Rome Flip Analyzer</h2>"
            "<p style='color: #E8956A; font-size: 0.9em; margin-top: 0;'>Pand Detail</p>",
            unsafe_allow_html=True,
        )
    with dm_col2:
        dark_mode = st.toggle(
            "Donker",
            value=st.session_state.get("dark_mode", False),
            key="detail_dark_toggle",
        )
        if dark_mode != st.session_state.get("dark_mode", False):
            st.session_state["dark_mode"] = dark_mode
            st.rerun()
    st.divider()

    # render_property_detail handles PDF export internally via _render_actions
    render_property_detail(listing, analysis, score_data, params)
    return True


def _run_belgium_flow(params_rome: dict, user: dict | None, auth_enabled: bool):
    """Volledige flow voor de Belgische vastgoedanalyse."""
    from config import DEFAULT_PARAMS_BE, get_score_label_be
    from services.immoweb_client import run_immoweb_scraper, validate_immoweb_url
    from models.financial_be import calculate_investment_analysis_be, calculate_sensitivity_be
    from models.scoring_be import calculate_flip_score_be
    from utils.helpers import format_eur, format_pct, format_m2, format_eur_per_m2, score_color

    params = st.session_state.get("params_be", DEFAULT_PARAMS_BE.copy())

    # === SIDEBAR: IMMOWEB ZOEK-URL ===
    st.sidebar.divider()
    st.sidebar.markdown("### Immoweb Data Invoer")

    # API Key
    api_key = ""
    try:
        api_key = st.secrets["apify"]["api_key"]
        st.sidebar.caption("Apify API: verbonden via secrets.toml")
    except (KeyError, AttributeError, FileNotFoundError):
        api_key = st.sidebar.text_input(
            "Apify API Key", type="password",
            value=st.session_state.get("apify_key", ""),
            key="be_apify_key",
        )

    search_url = st.sidebar.text_input(
        "Immoweb Zoek-URL",
        placeholder="https://www.immoweb.be/nl/zoeken/appartement/te-koop/antwerpen/2018",
        key="be_search_url",
    )
    max_results = st.sidebar.number_input(
        "Max. resultaten", value=50, min_value=5, max_value=500, step=25, key="be_max_results",
    )

    if st.sidebar.button("Scrape & Analyseer", key="be_scrape_btn", use_container_width=True):
        if not api_key:
            st.sidebar.error("Apify API key is vereist voor Immoweb.")
        elif not search_url:
            st.sidebar.error("Voer een Immoweb zoek-URL in.")
        else:
            try:
                raw = run_immoweb_scraper(api_key, search_url, max_results)
                if raw:
                    analyzed = _analyze_listings_be(raw, params)
                    st.session_state["analyzed_listings_be"] = analyzed
                    st.session_state["selected_property_idx_be"] = None
                    st.sidebar.success(f"{len(analyzed)} panden geanalyseerd!")
                else:
                    st.sidebar.warning("Geen resultaten gevonden.")
            except Exception as e:
                st.sidebar.error(f"Fout: {e}")

    # === MAIN CONTENT ===
    analyzed = st.session_state.get("analyzed_listings_be", [])

    TAB_NAMES = ["Dashboard", "Pand Detail", "Instellingen", "Wijkdata"]
    active_tab = st.session_state.get("active_tab_be", "Dashboard")
    if active_tab not in TAB_NAMES:
        active_tab = "Dashboard"

    tab_cols = st.columns(len(TAB_NAMES))
    for i, name in enumerate(TAB_NAMES):
        with tab_cols[i]:
            is_active = name == active_tab
            btn_type = "primary" if is_active else "secondary"
            if st.button(name, key=f"be_tab_{name}", use_container_width=True, type=btn_type):
                if not is_active:
                    st.session_state["active_tab_be"] = name
                    st.rerun()

    st.divider()

    # --- TAB 1: DASHBOARD ---
    if active_tab == "Dashboard":
        if analyzed:
            _render_be_dashboard(analyzed, params)
        else:
            st.markdown(
                """
                ### Welkom bij Nymos Flip Analyzer — België

                Gebruik de zijbalk om te beginnen:
                1. **Plak een Immoweb zoek-URL** (bv. appartementen te koop in Antwerpen 2018)
                2. De tool scrapt alle listings via Apify
                3. Elke listing wordt volledig geanalyseerd: ARV, P&L, Flip Score

                **Focus:** Antwerpen stad + Zuidrand.
                **Structuur:** BV (besloten vennootschap), bruto winst vóór VenB.
                """
            )

    # --- TAB 2: PAND DETAIL ---
    elif active_tab == "Pand Detail":
        if analyzed:
            options = [
                f"#{i+1} — Score {l.get('flip_score', 0)} — {l.get('zone', '?')} — {format_eur(l['price'])}"
                for i, l in enumerate(analyzed)
            ]
            idx = st.session_state.get("selected_property_idx_be", 0) or 0
            selected = st.selectbox("Selecteer pand", options, index=min(idx, len(options) - 1), key="be_select")
            sel_idx = options.index(selected)
            listing = analyzed[sel_idx]
            _render_be_property_detail(listing, params)
        else:
            st.info("Laad eerst data via de zijbalk.")

    # --- TAB 3: INSTELLINGEN ---
    elif active_tab == "Instellingen":
        _render_be_settings(params)

    # --- TAB 4: WIJKDATA ---
    elif active_tab == "Wijkdata":
        _render_be_neighborhood_view()


def _analyze_listings_be(raw_listings: list[dict], params: dict) -> list[dict]:
    """Analyseert Belgische listings."""
    from models.financial_be import calculate_investment_analysis_be
    from models.scoring_be import calculate_flip_score_be

    analyzed = []
    for listing in raw_listings:
        if not listing.get("is_in_scope", True):
            continue
        if listing.get("living_area", 0) < 30:
            continue

        analysis = calculate_investment_analysis_be(listing, params)
        score_data = calculate_flip_score_be(listing, analysis, params)

        enriched = listing.copy()
        enriched["analysis"] = analysis
        enriched["score_data"] = score_data
        enriched["flip_score"] = score_data["flip_score"]
        enriched["roi"] = analysis.get("roi", 0)
        enriched["gross_profit"] = analysis.get("gross_profit", 0)
        enriched["arv"] = analysis.get("arv", 0)
        enriched["risk_flags"] = score_data.get("risk_flags", [])
        enriched["total_investment"] = analysis.get("total_investment", 0)

        analyzed.append(enriched)

    analyzed.sort(key=lambda x: x["flip_score"], reverse=True)
    return analyzed


def _render_be_dashboard(listings: list[dict], params: dict):
    """Rendert het Belgische dashboard."""
    from utils.helpers import format_eur, format_pct, format_eur_per_m2, score_color
    from config import get_score_label_be

    total = len(listings)
    good_deals = sum(1 for l in listings if l.get("flip_score", 0) >= 60)
    avg_roi = sum(l.get("roi", 0) for l in listings) / total if total else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Panden", total)
    with col2:
        st.metric("Score >= 60", good_deals)
    with col3:
        st.metric("Gem. ROI (BV)", format_pct(avg_roi))
    with col4:
        best = max(listings, key=lambda l: l.get("flip_score", 0))
        st.metric("Beste deal", f"Score: {best.get('flip_score', 0)}")

    st.divider()

    # Sorteeropties
    BE_SORT_OPTIONS = {
        "Flip Score (hoog → laag)": ("flip_score", True),
        "Flip Score (laag → hoog)": ("flip_score", False),
        "Prijs (laag → hoog)": ("price", False),
        "Prijs (hoog → laag)": ("price", True),
        "Prijs/m² (laag → hoog)": ("price_per_sqm", False),
        "Prijs/m² (hoog → laag)": ("price_per_sqm", True),
        "ROI (hoog → laag)": ("roi", True),
        "ROI (laag → hoog)": ("roi", False),
        "Winst (hoog → laag)": ("gross_profit", True),
        "Winst (laag → hoog)": ("gross_profit", False),
        "Oppervlakte (groot → klein)": ("living_area", True),
        "Oppervlakte (klein → groot)": ("living_area", False),
    }

    sort_col, header_col = st.columns([1, 2])
    with header_col:
        st.subheader("Alle Panden")
    with sort_col:
        sort_label = st.selectbox(
            "Sorteren op",
            list(BE_SORT_OPTIONS.keys()),
            index=0,
            key="be_dashboard_sort",
        )
    sort_field, sort_reverse = BE_SORT_OPTIONS[sort_label]

    def _sort_val(item):
        val = item.get(sort_field)
        if val is None:
            return (1, 0)
        return (0, -val) if sort_reverse else (0, val)

    sorted_listings = sorted(listings, key=_sort_val)

    # Property cards
    COLS = 3
    for row_start in range(0, len(sorted_listings), COLS):
        row = sorted_listings[row_start:row_start + COLS]
        cols = st.columns(COLS)
        for col_idx, listing in enumerate(row):
            with cols[col_idx]:
                score = listing.get("flip_score", 0)
                label, color, _ = get_score_label_be(score)
                roi = listing.get("roi", 0)
                profit = listing.get("gross_profit", 0)

                with st.container(border=True):
                    # Foto
                    images = listing.get("images", [])
                    if images:
                        st.image(images[0], use_container_width=True)

                    # Score badge
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
                        f'<span style="background:linear-gradient(135deg,{color},{color}cc);color:white;'
                        f'padding:5px 14px;border-radius:10px;font-weight:700;font-size:1.05em;'
                        f'font-family:Inter,sans-serif;">{score}</span>'
                        f'<span style="color:#64748B;font-size:0.82em;font-weight:500;">{label}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # Info
                    zone = listing.get("zone", "?")
                    st.markdown(f"**{zone[:35]}**")
                    if listing.get("address"):
                        st.caption(listing["address"][:50])

                    st.markdown(
                        f"{format_eur(listing['price'])} | "
                        f"{listing.get('living_area', 0):.0f}m² | "
                        f"{format_eur_per_m2(listing.get('price_per_sqm', 0))}"
                    )

                    # ROI + Winst
                    roi_color = "green" if roi > 20 else "orange" if roi > 10 else "red"
                    st.markdown(f"**ROI (BV):** :{roi_color}[{format_pct(roi)}]")
                    profit_color = "green" if profit > 0 else "red"
                    st.markdown(f"**Winst:** :{profit_color}[{format_eur(profit)}]")

                    # Renovatieniveau
                    reno = listing.get("analysis", {}).get("renovation_estimate", {})
                    if reno:
                        st.caption(f"Renovatie: {reno.get('level_label', '?')} — {format_eur(reno.get('total_cost', 0))}")

                    if st.button("Bekijk detail", key=f"be_card_{row_start + col_idx}", use_container_width=True):
                        st.session_state["selected_property_idx_be"] = row_start + col_idx
                        st.session_state["active_tab_be"] = "Pand Detail"
                        st.rerun()


def _render_be_property_detail(listing: dict, params: dict):
    """Rendert de Belgische detailpagina voor een pand."""
    from utils.helpers import format_eur, format_pct, format_m2, format_eur_per_m2, score_color
    from config import get_score_label_be
    from models.financial_be import calculate_investment_analysis_be, calculate_sensitivity_be
    from models.scoring_be import calculate_flip_score_be
    from data.constants_be import CONDITION_LABELS_BE
    import plotly.graph_objects as go

    analysis = listing.get("analysis", {})
    score_data = listing.get("score_data", {})
    score = score_data.get("flip_score", 0)
    label, color, meaning = get_score_label_be(score)

    # === HEADER ===
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=score,
            number={"font": {"size": 48, "color": color}},
            title={"text": label, "font": {"size": 12, "color": "#94A3B8"}},
            gauge={"axis": {"range": [0, 100], "visible": False},
                   "bar": {"color": color}, "bgcolor": "#F3F0EC"},
        ))
        fig.update_layout(height=200, margin=dict(t=25, b=5, l=15, r=15),
                         paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(f"### {listing.get('address', listing.get('zone', 'Onbekend'))}")
        info = []
        if listing.get("zone"):
            info.append(f"**Wijk:** {listing['zone']}")
        cond_label = CONDITION_LABELS_BE.get(listing.get("condition", ""), listing.get("condition", ""))
        if cond_label:
            info.append(f"**Staat:** {cond_label}")
        if listing.get("epc_score"):
            info.append(f"**EPC:** {listing['epc_score']}")
        if listing.get("construction_year"):
            info.append(f"**Bouwjaar:** {listing['construction_year']}")
        st.markdown(" | ".join(info))
    with col3:
        st.metric("Vraagprijs", format_eur(listing["price"]))
        st.metric("Oppervlakte", f"{listing.get('living_area', 0):.0f} m²")
        st.metric("Prijs/m²", format_eur_per_m2(listing.get("price_per_sqm", 0)))

    st.divider()

    # === P&L TABEL ===
    st.subheader("Winst & Verliesrekening (BV)")

    pnl_html = '<div style="border-radius:16px;overflow:hidden;border:1px solid rgba(0,0,0,0.04);font-family:Inter,sans-serif;font-size:0.9rem;">'
    pnl_html += '<table style="width:100%;border-collapse:collapse;">'
    pnl_html += '<thead><tr style="background:#F8FAFC;">'
    pnl_html += '<th style="padding:12px 16px;text-align:left;font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.06em;color:#94A3B8;border-bottom:1px solid rgba(0,0,0,0.06);">Post</th>'
    pnl_html += '<th style="padding:12px 16px;text-align:right;font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.06em;color:#94A3B8;border-bottom:1px solid rgba(0,0,0,0.06);">Bedrag</th>'
    pnl_html += '</tr></thead><tbody>'

    def _pnl_row(label, value, bold=False, section=False):
        fw = "700" if bold else "400"
        if section:
            return f'<tr><td colspan="2" style="background:#1E1E2E;color:#E2E8F0;padding:10px 16px;font-weight:700;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em;">{label}</td></tr>'
        val_color = ""
        if bold and "WINST" in label.upper():
            val_num = analysis.get("gross_profit", 0)
            val_color = f"color:{'#10B981' if val_num >= 0 else '#EF4444'};"
        return f'<tr><td style="padding:10px 16px;font-weight:{fw};border-bottom:1px solid rgba(0,0,0,0.04);">{label}</td><td style="padding:10px 16px;text-align:right;font-weight:{fw};border-bottom:1px solid rgba(0,0,0,0.04);{val_color}">{value}</td></tr>'

    pnl_html += _pnl_row("AANKOOPZIJDE", "", section=True)
    pnl_html += _pnl_row("Aankoopprijs (na onderhandeling)", format_eur(analysis.get("purchase_price", 0)))
    pnl_html += _pnl_row(f"Registratierechten ({analysis.get('registration_tax_rate', 0.06)*100:.0f}%)", format_eur(analysis.get("registration_tax", 0)))
    pnl_html += _pnl_row("Notariskosten aankoop", format_eur(analysis.get("notary_buy", 0)))
    pnl_html += _pnl_row("Hypothecaire inschrijving", format_eur(analysis.get("mortgage_inscription", 0)))
    pnl_html += _pnl_row("Renovatiekosten", format_eur(analysis.get("renovation_cost", 0)))
    pnl_html += _pnl_row("Holding costs", format_eur(analysis.get("holding_costs", 0)))
    pnl_html += _pnl_row("Financieringskosten", format_eur(analysis.get("financing_costs", 0)))
    pnl_html += _pnl_row("TOTALE INVESTERING", format_eur(analysis.get("total_investment", 0)), bold=True)

    pnl_html += _pnl_row("VERKOOPZIJDE", "", section=True)
    pnl_html += _pnl_row("Geschatte verkoopprijs (ARV)", format_eur(analysis.get("arv", 0)))
    pnl_html += _pnl_row("Makelaar verkoop (3% + 21% BTW)", format_eur(analysis.get("broker_sell", 0)))
    pnl_html += _pnl_row("Notariskosten verkoop", format_eur(analysis.get("notary_sell", 0)))

    pnl_html += _pnl_row("BRUTO WINST (BV)", format_eur(analysis.get("gross_profit", 0)), bold=True)
    pnl_html += _pnl_row("ROI", format_pct(analysis.get("roi", 0)), bold=True)

    pnl_html += '</tbody></table></div>'
    st.markdown(pnl_html, unsafe_allow_html=True)

    st.divider()

    # === SCORE BREAKDOWN ===
    st.subheader("Flip Score Breakdown")
    comp = score_data.get("component_scores", {})
    explanations = score_data.get("score_explanations", {})
    weights = score_data.get("weights", {})

    categories = ["Prijs/m²", "ROI", "Locatie", "Risico", "Liquiditeit", "Oppervlakte"]
    keys = ["price_m2", "roi", "location", "risk", "liquidity", "surface"]
    values = [comp.get(k, 0) for k in keys]

    # Radar
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], theta=categories + [categories[0]],
        fill="toself", line_color="#818CF8", fillcolor="rgba(129,140,248,0.12)",
    ))
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False, height=350,
        margin=dict(l=60, r=60, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    for cat, key in zip(categories, keys):
        val = comp.get(key, 0)
        w = weights.get(key, 0) * 100
        with st.expander(f"{cat}: {val}/100 (gewicht: {w:.0f}%)"):
            st.markdown(explanations.get(key, "Geen toelichting."))

    st.divider()

    # === RISICOVLAGGEN ===
    st.subheader("Risicovlaggen")
    flags = score_data.get("risk_flags", [])
    if not flags:
        st.markdown(
            '<div style="background:rgba(16,185,129,0.06);border-left:4px solid #10B981;'
            'border-radius:0 12px 12px 0;padding:14px 18px;color:#059669;">'
            'Geen risicovlaggen.</div>',
            unsafe_allow_html=True,
        )
    else:
        for flag in flags:
            st.markdown(
                f'<div style="background:rgba(249,115,22,0.06);border-left:4px solid #F97316;'
                f'border-radius:0 12px 12px 0;padding:14px 18px;margin:8px 0;color:#9A3412;">'
                f'{flag}</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # === GEVOELIGHEIDSANALYSE ===
    st.subheader("Gevoeligheidsanalyse")
    scenarios = calculate_sensitivity_be(listing, params)
    sens_html = '<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif;font-size:0.9rem;">'
    sens_html += '<tr style="background:#F8FAFC;"><th style="padding:10px;text-align:left;">Scenario</th><th style="padding:10px;text-align:right;">ROI</th><th style="padding:10px;text-align:right;">Winst</th><th style="padding:10px;text-align:right;">Delta ROI</th></tr>'
    for s in scenarios:
        delta_color = "#10B981" if s["delta_roi"] >= 0 else "#EF4444"
        sens_html += f'<tr><td style="padding:10px;border-bottom:1px solid rgba(0,0,0,0.04);">{s["scenario"]}</td>'
        sens_html += f'<td style="padding:10px;text-align:right;border-bottom:1px solid rgba(0,0,0,0.04);">{format_pct(s["roi"])}</td>'
        sens_html += f'<td style="padding:10px;text-align:right;border-bottom:1px solid rgba(0,0,0,0.04);">{format_eur(s["profit"])}</td>'
        sens_html += f'<td style="padding:10px;text-align:right;border-bottom:1px solid rgba(0,0,0,0.04);color:{delta_color};">{s["delta_roi"]:+.1f}%</td></tr>'
    sens_html += '</table>'
    st.markdown(sens_html, unsafe_allow_html=True)

    # Break-even
    be_arv = analysis.get("break_even_arv", 0)
    if be_arv:
        st.info(f"**Break-even verkoopprijs:** {format_eur(be_arv)}")

    # Immoweb link
    if listing.get("url"):
        st.divider()
        st.link_button("Open op Immoweb", listing["url"], use_container_width=True)


def _render_be_settings(params: dict):
    """Belgische instellingen panel."""
    from config import DEFAULT_PARAMS_BE, PARAM_DESCRIPTIONS_BE

    st.subheader("Belgische Parameters")
    st.caption("Pas de parameters aan voor de Belgische vastgoedanalyse.")

    updated = params.copy()
    for key, (label, desc) in PARAM_DESCRIPTIONS_BE.items():
        if key not in params:
            continue
        val = params[key]
        if isinstance(val, float) and val < 1:
            updated[key] = st.slider(label, 0.0, 1.0, val, 0.01, help=desc, key=f"be_set_{key}")
        elif isinstance(val, float):
            updated[key] = st.number_input(label, value=val, help=desc, key=f"be_set_{key}")
        elif isinstance(val, int):
            updated[key] = st.number_input(label, value=val, help=desc, key=f"be_set_{key}")
        elif isinstance(val, str) and key == "region":
            updated[key] = st.selectbox(label, ["VLAANDEREN", "BRUSSEL", "WALLONIE"],
                                        index=["VLAANDEREN", "BRUSSEL", "WALLONIE"].index(val),
                                        help=desc, key=f"be_set_{key}")

    if updated != params:
        st.session_state["params_be"] = updated
        if st.session_state.get("analyzed_listings_be"):
            with st.spinner("Herberekenen..."):
                raw = st.session_state.get("analyzed_listings_be", [])
                st.session_state["analyzed_listings_be"] = _analyze_listings_be(raw, updated)


def _render_be_neighborhood_view():
    """Belgische wijkdata overzicht."""
    from data.neighborhoods_be import ALL_NEIGHBORHOODS_BE
    import pandas as pd

    st.subheader("Wijkbenchmarks — Antwerpen & Zuidrand")

    rows = []
    for name, data in ALL_NEIGHBORHOODS_BE.items():
        rows.append({
            "Wijk": name,
            "Tier": data["tier"],
            "Score": data["score"],
            "App. €/m² (laag)": f"€{data['apt_price_low']:,}",
            "App. €/m² (mid)": f"€{data['apt_price_mid']:,}",
            "App. €/m² (hoog)": f"€{data['apt_price_high']:,}",
            "Huis €/m² (mid)": f"€{data['house_price_mid']:,}",
            "Opmerkingen": data["notes"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def main():
    """Hoofdfunctie van de applicatie."""
    init_session_state()

    # === DIRECT DETAIL LINK (new browser tab) — no auth needed ===
    if _handle_direct_detail_link():
        return

    # === AUTH GATE ===
    auth_enabled = _has_supabase_config()
    if auth_enabled:
        restore_session()
        if not is_logged_in():
            render_auth_page()
            return

    params = st.session_state["params"]
    user = get_current_user() if auth_enabled else None

    # === SIDEBAR ===
    st.sidebar.markdown(
        "<h2 style='color: #1A1A2E; margin-bottom: 0; font-family: Inter, sans-serif; font-weight: 700;'>"
        "Nymos Flip Analyzer</h2>"
        "<p style='color: #E8956A; font-size: 0.9em; margin-top: 4px; font-family: Inter, sans-serif;'>"
        "Vastgoed Investeringsanalyse</p>",
        unsafe_allow_html=True,
    )

    # Country selector — duidelijk zichtbaar als selectbox
    st.sidebar.divider()
    country_choice = st.sidebar.selectbox(
        "Selecteer markt",
        ["🇮🇹 Rome (Italië)", "🇧🇪 Antwerpen (België)"],
        index=0 if st.session_state.get("country", "IT") == "IT" else 1,
        key="country_select",
    )
    new_country = "BE" if "België" in country_choice else "IT"
    if new_country != st.session_state.get("country", "IT"):
        st.session_state["country"] = new_country
        st.rerun()
    st.session_state["country"] = new_country
    st.sidebar.divider()

    # Dark mode toggle
    dark_mode = st.sidebar.toggle(
        "Donkere modus",
        value=st.session_state.get("dark_mode", False),
        key="dark_mode_toggle",
    )
    if dark_mode != st.session_state.get("dark_mode", False):
        st.session_state["dark_mode"] = dark_mode
        st.rerun()

    # User info + uitlogknop
    if user:
        st.sidebar.caption(f"Ingelogd als: {user['email']}")
        if st.sidebar.button("Uitloggen", use_container_width=True):
            logout()
            st.rerun()

    # Zoek-/invoerpaneel — afhankelijk van geselecteerde markt
    is_belgium = st.session_state.get("country") == "BE"

    if is_belgium:
        _run_belgium_flow(params, user, auth_enabled)
        return

    # --- ROME FLOW (bestaand) ---
    new_listings = render_search_panel()

    # Verwerk nieuwe listings
    if new_listings:
        st.session_state["raw_listings"] = new_listings
        with st.spinner("Bezig met analyseren..."):
            st.session_state["analyzed_listings"] = analyze_listings(new_listings, params)
        st.session_state["selected_property_idx"] = None
        st.session_state["property_overrides"] = {}

        # Auto-save naar database
        if user:
            search_type = st.session_state.get("last_search_type", "url")
            search_query = st.session_state.get("last_search_query", "")
            search_id = save_search(
                user_id=user["id"],
                search_type=search_type,
                search_query=search_query,
                analyzed_listings=st.session_state["analyzed_listings"],
            )
            if search_id:
                st.session_state["last_search_id"] = search_id

    # Zoekgeschiedenis
    if auth_enabled:
        history_listings = render_search_history()
        if history_listings:
            st.session_state["analyzed_listings"] = history_listings
            st.session_state["raw_listings"] = history_listings
            st.session_state["selected_property_idx"] = None
            st.session_state["property_overrides"] = {}
            st.rerun()

    # Filter bestaande resultaten
    analyzed = st.session_state.get("analyzed_listings", [])
    if analyzed:
        filtered = render_filters(analyzed, params)
    else:
        filtered = []

    # === HOOFDGEBIED ===
    TAB_NAMES = ["Dashboard", "Pand Detail", "Favorieten", "Instellingen", "Wijkdata"]
    active_tab = st.session_state.get("active_tab", "Dashboard")
    if active_tab not in TAB_NAMES:
        active_tab = "Dashboard"

    # Tab bar
    tab_cols = st.columns(len(TAB_NAMES))
    for i, name in enumerate(TAB_NAMES):
        with tab_cols[i]:
            is_active = name == active_tab
            btn_type = "primary" if is_active else "secondary"
            if st.button(name, key=f"tab_{name}", use_container_width=True, type=btn_type):
                if not is_active:
                    st.session_state["active_tab"] = name
                    st.rerun()

    st.divider()

    # --- TAB 1: DASHBOARD ---
    if active_tab == "Dashboard":
        if filtered:
            selected_idx = render_dashboard(filtered)
            if selected_idx is not None:
                st.session_state["selected_property_idx"] = selected_idx
                st.session_state["active_tab"] = "Pand Detail"
                st.rerun()

            # Batch PDF export
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Exporteer Batch PDF", use_container_width=True):
                    with st.spinner("PDF genereren..."):
                        pdf_bytes = generate_batch_report(filtered, params)
                    st.download_button(
                        label="Download Batch Rapport",
                        data=pdf_bytes,
                        file_name="rome_flip_batch_rapport.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
        else:
            st.markdown(
                """
                ### Welkom bij Rome Flip Analyzer

                Gebruik de zijbalk om te beginnen:
                1. **Zoek-URL Scrapen** -- Plak een Immobiliare.it zoek-URL
                2. **Enkel Pand** -- Analyseer een specifiek pand
                3. **Upload** -- Upload een bestand met listings
                4. **Testdata** -- Laad voorbeelddata om de tool te verkennen

                De tool berekent voor elk pand:
                - Volledige P&L (prima casa + seconda casa scenario)
                - Flip Score (0-100) met onderbouwde toelichting
                - Locatieanalyse op basis van wijk, verdieping, lift, terras, etc.
                - Verkoopprijsschatting met onderbouwing per pandfactor
                """
            )

    # --- TAB 2: PAND DETAIL ---
    elif active_tab == "Pand Detail":
        idx = st.session_state.get("selected_property_idx")

        if analyzed:
            if st.button("← Terug naar Dashboard", key="back_to_dashboard"):
                st.session_state["active_tab"] = "Dashboard"
                st.rerun()
            options = [
                f"#{i+1} -- Score {l['flip_score']} -- {l.get('zone', 'Onbekend')} -- {l.get('price', 0):,.0f} EUR"
                for i, l in enumerate(analyzed)
            ]
            selected_option = st.selectbox(
                "Selecteer een pand",
                options,
                index=idx if idx is not None and idx < len(options) else 0,
            )
            selected_idx = options.index(selected_option)
            listing = analyzed[selected_idx]

            # render_property_detail handles slider overrides, recalculation, and PDF export internally
            render_property_detail(listing, listing["analysis"], listing["score_data"], params)
        else:
            st.info("Laad eerst data via de zijbalk om een pand te analyseren.")

    # --- TAB 3: FAVORIETEN ---
    elif active_tab == "Favorieten":
        selected_fav = render_favorites()
        if selected_fav:
            # Gebruiker wil een favoriet bekijken — toon detail
            analysis = selected_fav.get("analysis", {})
            score_data = selected_fav.get("score_data", {})
            if analysis and score_data:
                st.divider()
                render_property_detail(selected_fav, analysis, score_data, params)
            else:
                st.warning("Analysedata niet beschikbaar voor dit opgeslagen pand.")

    # --- TAB 4: INSTELLINGEN ---
    elif active_tab == "Instellingen":
        updated_params = render_settings(params)
        if updated_params != params:
            st.session_state["params"] = updated_params
            if st.session_state.get("raw_listings"):
                with st.spinner("Herberekenen met nieuwe parameters..."):
                    st.session_state["analyzed_listings"] = analyze_listings(
                        st.session_state["raw_listings"], updated_params
                    )

    # --- TAB 5: WIJKDATA ---
    elif active_tab == "Wijkdata":
        render_neighborhood_view()


if __name__ == "__main__":
    main()
