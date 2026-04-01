"""
Apify API integratie voor het scrapen van Immobiliare.it listings.

Actor: shahidirfan/immobiliare-it-scraper (GRATIS)
Input: startUrl (string), results_wanted (int), max_pages (int)
Output: Plat formaat met price_value, surface, macrozone, etc.
"""
from __future__ import annotations

import time
import requests
import streamlit as st

APIFY_BASE_URL = "https://api.apify.com/v2"

# Gratis actor voor Immobiliare.it scraping
SEARCH_ACTOR_ID = "shahidirfan~immobiliare-it-scraper"


def run_immobiliare_scraper(api_key: str, url: str, max_pages: int = 5, max_results: int = 100) -> list[dict]:
    """
    Roept de Apify Immobiliare.it scraper aan.

    Args:
        api_key: Apify API token.
        url: Een Immobiliare.it zoek-URL of listing-URL.
        max_pages: Maximum aantal pagina's te scrapen (1-20).
        max_results: Maximum aantal resultaten.

    Returns:
        Lijst van ruwe listing-dicts van Apify.
    """
    is_valid, url_type = validate_immobiliare_url(url)
    if not is_valid:
        raise ValueError("Ongeldige Immobiliare.it URL")

    run_input = {
        "startUrl": url,
        "max_pages": min(max(1, max_pages), 20),
        "results_wanted": max_results,
    }

    return _run_actor(api_key, SEARCH_ACTOR_ID, run_input)


def _run_actor(api_key: str, actor_id: str, run_input: dict) -> list[dict]:
    """
    Start een Apify actor, wacht tot die klaar is, en haalt de resultaten op.
    """
    # Start de actor run
    response = requests.post(
        f"{APIFY_BASE_URL}/acts/{actor_id}/runs",
        params={"token": api_key},
        json=run_input,
        timeout=30,
    )
    response.raise_for_status()
    run_data = response.json()["data"]
    run_id = run_data["id"]
    dataset_id = run_data["defaultDatasetId"]

    # Polling: wacht tot run klaar is (max ~5 minuten)
    progress_bar = st.progress(0, text="Apify scraper draait...")
    for i in range(60):
        status_resp = requests.get(
            f"{APIFY_BASE_URL}/actor-runs/{run_id}",
            params={"token": api_key},
            timeout=15,
        )
        status_resp.raise_for_status()
        status = status_resp.json()["data"]["status"]

        if status == "SUCCEEDED":
            progress_bar.progress(100, text="Scraping voltooid!")
            break
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            progress_bar.empty()
            raise Exception(f"Apify run mislukt met status: {status}")

        progress_bar.progress(
            min(95, int((i / 60) * 100)),
            text=f"Apify scraper draait... ({status})",
        )
        time.sleep(5)
    else:
        progress_bar.empty()
        raise Exception("Apify run timeout na 5 minuten")

    # Haal resultaten op
    results_resp = requests.get(
        f"{APIFY_BASE_URL}/datasets/{dataset_id}/items",
        params={"token": api_key, "format": "json"},
        timeout=60,
    )
    results_resp.raise_for_status()
    results = results_resp.json()

    progress_bar.empty()

    if not results:
        st.warning("Geen resultaten gevonden van Apify scraper.")
        return []

    return results


def validate_immobiliare_url(url: str) -> tuple[bool, str]:
    """
    Valideert of de URL een geldige Immobiliare.it URL is.

    Returns:
        (is_valid, url_type) waar url_type "search" of "listing" is.
    """
    url = url.strip()
    if not url.startswith("https://www.immobiliare.it") and not url.startswith("http://www.immobiliare.it"):
        return False, ""

    if "/annunci/" in url or "/annuncio/" in url:
        return True, "listing"
    elif "/vendita-case/" in url or "/vendita-appartamenti/" in url or "/affitto-case/" in url:
        return True, "search"

    # Accepteer ook andere Immobiliare.it URLs als zoek-URL
    return True, "search"
