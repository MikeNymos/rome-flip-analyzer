"""
Zoek/filter interface in de zijbalk.
"""
from __future__ import annotations


import re
import streamlit as st

from services.apify_client import run_immobiliare_scraper, validate_immobiliare_url
from services.parser import parse_uploaded_file, parse_json_data, filter_valid_listings


def _sanitize_url(raw: str) -> str:
    """
    Schoont een door de gebruiker ingeplakte URL op.
    Verwijdert: dubbele URLs, fragmenten (#foto20), witruimte, URL-encoded troep.
    """
    raw = raw.strip()
    if not raw:
        return raw

    # Verwijder fragment
    raw = raw.split("#")[0].strip()

    # Detecteer dubbel-geplakte URLs
    parts = re.split(r'(?=https?://)', raw)
    valid = [p.strip() for p in parts if p.strip() and "immobiliare.it" in p]
    if valid:
        raw = max(valid, key=len)  # langste = meest compleet

    # Extraheer listing ID als het een annunci-URL is
    m = re.search(r'/annunc[io]+/(\d+)', raw)
    if m:
        return f"https://www.immobiliare.it/annunci/{m.group(1)}/"

    return raw.strip()


def render_search_panel():
    """
    Rendert het zoek/invoer-paneel in de sidebar.
    Retourneert een lijst van ruwe listings indien er nieuwe data is.
    """

    # API Key — laad automatisch uit secrets.toml indien beschikbaar
    secrets_key = ""
    try:
        secrets_key = st.secrets["apify"]["api_key"]
    except (KeyError, AttributeError, FileNotFoundError):
        pass

    if secrets_key:
        api_key = secrets_key
        st.sidebar.markdown("### Apify API Key")
        st.sidebar.caption("Verbonden via secrets.toml")
    else:
        st.sidebar.markdown("### Apify API Key")
        api_key = st.sidebar.text_input(
            "API Key",
            type="password",
            value=st.session_state.get("apify_key", ""),
            help="Voer je Apify API key in voor het scrapen van Immobiliare.it",
            label_visibility="collapsed",
        )
        if api_key:
            st.session_state["apify_key"] = api_key

    st.sidebar.divider()
    st.sidebar.markdown("### Data Invoer")

    tab1, tab2, tab3 = st.sidebar.tabs(["Zoek-URL", "Enkel Pand", "Upload"])

    new_listings = None

    # === TAB 1: ZOEK-URL SCRAPEN ===
    with tab1:
        st.markdown("Plak een Immobiliare.it **zoek-URL** met filters.")
        search_url = st.text_input(
            "Zoek-URL",
            placeholder="https://www.immobiliare.it/vendita-case/roma/prati/?prezzoMassimo=650000",
            key="search_url_input",
            label_visibility="collapsed",
        )
        max_results = st.number_input(
            "Max. resultaten", value=50, min_value=5, max_value=500, step=25, key="max_results",
            help="Maximum aantal listings om op te halen.",
        )
        max_pages = st.number_input(
            "Max. pagina's", value=5, min_value=1, max_value=20, step=1, key="max_pages",
            help="Elke pagina bevat ~25 resultaten.",
        )
        if st.button("Scrape & Analyseer", key="btn_search", use_container_width=True):
            if not search_url:
                st.error("Voer een zoek-URL in.")
            else:
                is_valid, url_type = validate_immobiliare_url(search_url)
                if not is_valid:
                    st.error("Ongeldige URL. Voer een Immobiliare.it URL in.")
                else:
                    try:
                        raw_results = run_immobiliare_scraper(api_key, search_url, max_pages, max_results)
                        if raw_results:
                            # Direct scraper returns pre-normalized dicts for search URLs;
                            # Apify results (single listings) need parsing
                            if url_type == "search":
                                new_listings = raw_results
                            else:
                                new_listings = parse_json_data(raw_results)
                            st.session_state["last_search_type"] = "url"
                            st.session_state["last_search_query"] = search_url
                            st.success(f"{len(new_listings)} panden gevonden!")
                        else:
                            st.warning("Geen resultaten gevonden.")
                    except Exception as e:
                        st.error(f"Fout bij scraping: {e}")

    # === TAB 2: ENKEL PAND ===
    with tab2:
        st.markdown("Plak de URL van **één pand** op Immobiliare.it.")
        listing_url_raw = st.text_input(
            "Pand-URL",
            placeholder="https://www.immobiliare.it/annunci/127935180/",
            key="listing_url_input",
            label_visibility="collapsed",
        )
        if st.button("Analyseer Dit Pand", key="btn_listing", use_container_width=True):
            if not listing_url_raw:
                st.error("Voer een pand-URL in.")
            else:
                # Schoon URL op (verwijder #fragment, dubbele URLs, etc.)
                listing_url = _sanitize_url(listing_url_raw)
                st.caption(f"Opgeschoonde URL: `{listing_url}`")

                is_valid, url_type = validate_immobiliare_url(listing_url)
                if not is_valid:
                    st.error("Ongeldige URL. Voer een Immobiliare.it URL in.")
                else:
                    try:
                        with st.spinner("Pand ophalen..."):
                            raw_results = run_immobiliare_scraper(api_key, listing_url, max_pages=1)
                        if raw_results:
                            # Direct scraping returns pre-normalized dicts
                            if isinstance(raw_results[0], dict) and "price" in raw_results[0] and "surface_m2" in raw_results[0]:
                                new_listings = filter_valid_listings(raw_results)
                            else:
                                new_listings = parse_json_data(raw_results)
                            st.session_state["last_search_type"] = "single"
                            st.session_state["last_search_query"] = listing_url
                            st.success("Pand succesvol opgehaald!")
                        else:
                            st.warning("Geen data gevonden voor dit pand.")
                    except Exception as e:
                        st.error(f"Fout bij ophalen pand: {e}")

    # === TAB 3: BESTAND UPLOADEN ===
    with tab3:
        st.markdown("Upload een **JSON, CSV of XLSX** bestand met listings.")
        uploaded_file = st.file_uploader(
            "Kies bestand",
            type=["json", "csv", "xlsx", "xls"],
            key="file_uploader",
            label_visibility="collapsed",
        )
        if st.button("Upload & Analyseer", key="btn_upload", use_container_width=True):
            if uploaded_file is None:
                st.error("Selecteer eerst een bestand.")
            else:
                try:
                    new_listings = parse_uploaded_file(uploaded_file)
                    if new_listings:
                        st.session_state["last_search_type"] = "upload"
                        st.session_state["last_search_query"] = uploaded_file.name
                        st.success(f"{len(new_listings)} panden geladen!")
                    else:
                        st.warning("Geen geldige panden gevonden in bestand.")
                except Exception as e:
                    st.error(f"Fout bij verwerken bestand: {e}")

    # Testdata laden
    st.sidebar.divider()
    if st.sidebar.button("Laad Testdata", use_container_width=True, help="Laad voorbeelddata zonder API key"):
        try:
            import json as json_module
            import os
            sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data.json")
            with open(sample_path, "r") as f:
                sample_data = json_module.load(f)
            new_listings = parse_json_data(sample_data)
            st.session_state["last_search_type"] = "test"
            st.session_state["last_search_query"] = "sample_data.json"
            st.sidebar.success(f"{len(new_listings)} testpanden geladen!")
        except FileNotFoundError:
            st.sidebar.error("sample_data.json niet gevonden.")
        except Exception as e:
            st.sidebar.error(f"Fout bij laden testdata: {e}")

    # Filter valid listings
    if new_listings:
        new_listings = filter_valid_listings(new_listings)

    return new_listings


def render_filters(listings: list[dict], params: dict) -> list[dict]:
    """
    Rendert snelfilters in de sidebar en retourneert gefilterde listings.
    """
    if not listings:
        return listings

    st.sidebar.divider()
    st.sidebar.markdown("### Filters")

    # Wijk filter
    zones = sorted(set(l.get("zone", "Onbekend") for l in listings))
    selected_zones = st.sidebar.multiselect("Wijk", zones, default=zones)

    # Prijsrange
    prices = [l["price"] for l in listings]
    min_p, max_p = int(min(prices)), int(max(prices))
    if min_p < max_p:
        price_range = st.sidebar.slider(
            "Prijsrange (€)",
            min_value=min_p,
            max_value=max_p,
            value=(min_p, max_p),
            step=10000,
            format="€%d",
        )
    else:
        price_range = (min_p, max_p)

    # m² range
    surfaces = [l["surface_m2"] for l in listings]
    min_s, max_s = int(min(surfaces)), int(max(surfaces))
    if min_s < max_s:
        surface_range = st.sidebar.slider(
            "Oppervlakte (m²)",
            min_value=min_s,
            max_value=max_s,
            value=(min_s, max_s),
            step=5,
        )
    else:
        surface_range = (min_s, max_s)

    # Minimum flip score
    min_score = st.sidebar.slider(
        "Minimum Flip Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
    )

    # Filter toepassen
    filtered = [
        l for l in listings
        if l.get("zone", "Onbekend") in selected_zones
        and price_range[0] <= l["price"] <= price_range[1]
        and surface_range[0] <= l["surface_m2"] <= surface_range[1]
        and l.get("flip_score", 0) >= min_score
    ]

    st.sidebar.caption(f"{len(filtered)} van {len(listings)} panden getoond")

    return filtered
