"""
Rome Flip Analyzer — Hoofdapplicatie
Vastgoedanalyse-tool voor buy-renovate-sell investeringen in Rome.
"""
from __future__ import annotations

import streamlit as st

from config import DEFAULT_PARAMS, get_score_label
from models.financial import calculate_investment_analysis
from models.scoring import calculate_flip_score
from components.dashboard import render_dashboard
from components.property_detail import render_property_detail
from components.settings_panel import render_settings
from components.search_panel import render_search_panel, render_filters
from components.neighborhood_view import render_neighborhood_view
from components.auth_page import render_auth_page
from components.search_history import render_search_history
from services.pdf_export import generate_property_report, generate_batch_report
from services.auth import is_logged_in, get_current_user, logout, restore_session
from services.database import save_search


# === PAGINA CONFIGURATIE ===
st.set_page_config(
    page_title="Rome Flip Analyzer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === CUSTOM CSS ===
st.markdown("""
<style>
    .stApp > header { background-color: transparent; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px 16px;
    }
    div[data-testid="stMetric"] label { color: #1a365d; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; }
</style>
""", unsafe_allow_html=True)


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
    if "export_pdf" not in st.session_state:
        st.session_state["export_pdf"] = False
    if "property_overrides" not in st.session_state:
        st.session_state["property_overrides"] = {}


def analyze_listings(listings: list[dict], params: dict) -> list[dict]:
    """
    Draait de volledige analyse op alle listings:
    financieel model + scoring + locatie + verkoopprijsschatting.
    """
    analyzed = []
    for listing in listings:
        # Financiële analyse (inclusief locatie + verkoopprijsschatting)
        analysis = calculate_investment_analysis(listing, params)

        # Flip Score
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
    return analyzed


def _has_supabase_config() -> bool:
    """Controleert of Supabase credentials geconfigureerd zijn."""
    try:
        return bool(st.secrets.get("supabase", {}).get("url"))
    except (AttributeError, FileNotFoundError):
        return False


def main():
    """Hoofdfunctie van de applicatie."""
    init_session_state()

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
            save_search(
                user_id=user["id"],
                search_type=search_type,
                search_query=search_query,
                analyzed_listings=st.session_state["analyzed_listings"],
            )

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
    tab_dashboard, tab_detail, tab_settings, tab_neighborhoods = st.tabs([
        "Dashboard",
        "Pand Detail",
        "Instellingen",
        "Wijkdata",
    ])

    # --- TAB 1: DASHBOARD ---
    with tab_dashboard:
        if filtered:
            selected_idx = render_dashboard(filtered)
            if selected_idx is not None:
                st.session_state["selected_property_idx"] = selected_idx
                st.info("Klik op het tabblad **Pand Detail** om de volledige analyse te bekijken.")

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
    with tab_detail:
        idx = st.session_state.get("selected_property_idx")

        if analyzed:
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

            # Check per-pand overrides
            overrides = st.session_state.get("property_overrides", {}).get(listing.get("url", ""), {})

            if overrides:
                recalc_analysis = calculate_investment_analysis(listing, params, overrides)
                recalc_score = calculate_flip_score(listing, recalc_analysis, params)
                render_property_detail(listing, recalc_analysis, recalc_score, params)
            else:
                render_property_detail(listing, listing["analysis"], listing["score_data"], params)

            # PDF export
            if st.session_state.get("export_pdf"):
                st.session_state["export_pdf"] = False
                with st.spinner("PDF genereren..."):
                    pdf_bytes = generate_property_report(
                        listing, listing["analysis"], listing["score_data"], params,
                    )
                st.download_button(
                    label="Download PDF Rapport",
                    data=pdf_bytes,
                    file_name=f"flip_analyse_{listing.get('zone', 'pand')}_{listing.get('price', 0):.0f}.pdf",
                    mime="application/pdf",
                )
        else:
            st.info("Laad eerst data via de zijbalk om een pand te analyseren.")

    # --- TAB 3: INSTELLINGEN ---
    with tab_settings:
        updated_params = render_settings(params)
        if updated_params != params:
            st.session_state["params"] = updated_params
            if st.session_state.get("raw_listings"):
                with st.spinner("Herberekenen met nieuwe parameters..."):
                    st.session_state["analyzed_listings"] = analyze_listings(
                        st.session_state["raw_listings"], updated_params
                    )

    # --- TAB 4: WIJKDATA ---
    with tab_neighborhoods:
        render_neighborhood_view()


if __name__ == "__main__":
    main()
