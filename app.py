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
    """Injecteert CSS op basis van het huidige thema (light/dark)."""
    dark = st.session_state.get("dark_mode", False)

    common = """
    .stApp > header { background-color: transparent; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; }
    """

    if dark:
        theme = """
        /* ===== DARK MODE ===== */
        .stApp { background-color: #0e1117; }
        section[data-testid="stSidebar"] { background-color: #16192b; }
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stCaption p {
            color: #e2e8f0 !important;
        }

        /* Headings */
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 { color: #f7fafc !important; }

        /* Text */
        .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th,
        .stMarkdown strong, .stMarkdown em, .stMarkdown span {
            color: #e2e8f0 !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] p { color: #a0aec0 !important; }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background-color: #1a1f36 !important;
            border: 1px solid #2d3748 !important;
            border-radius: 8px;
            padding: 12px 16px;
        }
        div[data-testid="stMetric"] label { color: #a0aec0 !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #f7fafc !important; }
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] { color: #a0aec0 !important; }

        /* Inputs */
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            background-color: #1a1f36 !important;
            color: #e2e8f0 !important;
            border-color: #2d3748 !important;
        }
        .stTextInput label, .stNumberInput label, .stTextArea label,
        .stSelectbox label, .stSlider label, .stCheckbox label {
            color: #e2e8f0 !important;
        }
        [data-baseweb="select"] > div { background-color: #1a1f36 !important; }
        [data-baseweb="select"] span { color: #e2e8f0 !important; }
        [data-baseweb="popover"] > div { background-color: #1a1f36 !important; }
        [data-baseweb="menu"] { background-color: #1a1f36 !important; }
        [data-baseweb="menu"] li { color: #e2e8f0 !important; }
        [data-baseweb="menu"] li:hover { background-color: #2d3748 !important; }

        /* Expander */
        [data-testid="stExpander"] { border-color: #2d3748 !important; }
        .streamlit-expanderHeader, [data-testid="stExpanderToggleDetails"] summary span {
            color: #e2e8f0 !important;
        }

        /* Containers with border */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #2d3748 !important;
            background-color: #0e1117 !important;
        }

        /* Buttons */
        button[kind="secondary"] {
            background-color: #1a1f36 !important;
            color: #e2e8f0 !important;
            border-color: #2d3748 !important;
        }
        button[kind="primary"] {
            background-color: #2b6cb0 !important;
            color: white !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab"] { color: #a0aec0 !important; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #f7fafc !important; }
        .stTabs [data-baseweb="tab-border"] { background-color: #2d3748 !important; }
        .stTabs [data-baseweb="tab-highlight"] { background-color: #2b6cb0 !important; }

        /* Tables */
        .stMarkdown table { border-color: #2d3748 !important; }
        .stMarkdown table th { background-color: #16192b !important; color: #f7fafc !important; border-color: #2d3748 !important; }
        .stMarkdown table td { color: #e2e8f0 !important; border-color: #2d3748 !important; }

        /* Info/warning/success/error boxes */
        [data-testid="stAlert"] > div { background-color: #1a2332 !important; color: #e2e8f0 !important; }

        /* Divider */
        hr, [data-testid="stSeparator"] { border-color: #2d3748 !important; }

        /* Links */
        a { color: #63b3ed !important; }

        /* Download button */
        [data-testid="stDownloadButton"] button {
            background-color: #1a1f36 !important;
            color: #e2e8f0 !important;
            border-color: #2d3748 !important;
        }

        /* Form border */
        [data-testid="stForm"] { border-color: #2d3748 !important; }

        /* Slider track */
        [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
            background-color: #2b6cb0 !important;
        }

        /* Override inline styles on our custom HTML */
        .stApp [style*="color: #1a365d"],
        .stApp [style*="color:#1a365d"] { color: #90cdf4 !important; }
        .stApp [style*="color: #555"],
        .stApp [style*="color:#555"] { color: #a0aec0 !important; }
        .stApp [style*="color: #888"],
        .stApp [style*="color:#888"] { color: #718096 !important; }
        .stApp [style*="color: #c9a026"],
        .stApp [style*="color:#c9a026"] { color: #d4af37 !important; }
        .stApp [style*="background-color: #f8f9fa"],
        .stApp [style*="background:#f8f9fa"] { background-color: #1a1f36 !important; }
        .stApp [style*="border: 1px solid #e9ecef"],
        .stApp [style*="border:1px solid #e9ecef"] { border-color: #2d3748 !important; }
        .stApp [style*="color: rgb(49, 51, 63)"],
        .stApp [style*="color:rgb(49,51,63)"] { color: #e2e8f0 !important; }
        .stApp [style*="background-color:white"],
        .stApp [style*="background-color: white"] { background-color: #1a1f36 !important; }
        .stApp [style*="border: 1px solid rgba(49,51,63,0.2)"],
        .stApp [style*="border:1px solid rgba(49,51,63,0.2)"] { border-color: #2d3748 !important; }

        /* Spinner */
        [data-testid="stSpinner"] p { color: #a0aec0 !important; }
        """
    else:
        theme = """
        /* ===== LIGHT MODE ===== */
        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 12px 16px;
        }
        div[data-testid="stMetric"] label { color: #1a365d; }
        div[data-testid="stHorizontalBlock"] > div > div > button[kind="secondary"] {
            border-color: #e0e0e0;
        }
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
            "<h2 style='color: #1a365d; margin-bottom: 0;'>Rome Flip Analyzer</h2>"
            "<p style='color: #c9a026; font-size: 0.9em; margin-top: 0;'>Pand Detail</p>",
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
        "<h2 style='color: #1a365d; margin-bottom: 0;'>Rome Flip Analyzer</h2>"
        "<p style='color: #c9a026; font-size: 0.9em; margin-top: 0;'>Vastgoed Investeringsanalyse</p>",
        unsafe_allow_html=True,
    )

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

    # Zoek-/invoerpaneel
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
