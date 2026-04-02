"""
Immobiliare.it scraping module.

Primary method: Direct HTML scraping of Immobiliare.it search pages.
Extracts listing data from embedded __NEXT_DATA__ JSON (server-side rendered).
Fallback: Apify actor for individual listing URLs.
"""
from __future__ import annotations

import re
import json
import time
import requests
import streamlit as st
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

APIFY_BASE_URL = "https://api.apify.com/v2"
SEARCH_ACTOR_ID = "shahidirfan~immobiliare-it-scraper"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
}


def run_immobiliare_scraper(
    api_key: str, url: str, max_pages: int = 5, max_results: int = 100
) -> list[dict]:
    """
    Scrape Immobiliare.it listings from a search URL or single listing URL.

    For search URLs: scrapes directly from Immobiliare.it HTML (accurate results).
    For single listing URLs: uses Apify actor as fallback.
    """
    is_valid, url_type = validate_immobiliare_url(url)
    if not is_valid:
        raise ValueError("Ongeldige Immobiliare.it URL")

    if url_type == "search":
        return _scrape_search_direct(url, max_pages, max_results)
    else:
        # Single listing — use Apify actor
        return _run_actor(api_key, SEARCH_ACTOR_ID, {
            "startUrl": url,
            "max_pages": 1,
            "results_wanted": 1,
        })


def _scrape_search_direct(url: str, max_pages: int, max_results: int) -> list[dict]:
    """
    Directly scrape Immobiliare.it search results by fetching HTML pages
    and extracting the embedded __NEXT_DATA__ JSON.

    Some URLs (with SEO path segments like 'con-piani-intermedi') trigger
    client-side rendering, so we clean the URL first and post-filter results.
    """
    all_results = []
    progress_bar = st.progress(0, text="Immobiliare.it wordt gescraped...")

    # Try original URL first
    page_data = _fetch_search_page(url, page=1)

    # If no SSR data, try cleaned URL (strip SEO path segments)
    clean_url = url
    if not page_data:
        clean_url = _clean_search_url(url)
        if clean_url != url:
            page_data = _fetch_search_page(clean_url, page=1)

    if not page_data:
        progress_bar.empty()
        raise Exception("Kon geen data ophalen van Immobiliare.it. Controleer de URL.")

    total_count = page_data.get("count", 0)
    site_max_pages = page_data.get("maxPages", 1)
    actual_max_pages = min(max_pages, site_max_pages)

    results = page_data.get("results", [])
    all_results.extend(results)

    progress_bar.progress(
        min(95, int(100 / actual_max_pages)),
        text=f"Pagina 1/{actual_max_pages} opgehaald ({len(all_results)} listings)...",
    )

    # Fetch remaining pages (use clean_url for pagination)
    for page_num in range(2, actual_max_pages + 1):
        if len(all_results) >= max_results:
            break

        time.sleep(1)  # Be respectful to the server

        page_data = _fetch_search_page(clean_url, page=page_num)
        if not page_data:
            break

        results = page_data.get("results", [])
        if not results:
            break

        all_results.extend(results)
        progress_bar.progress(
            min(95, int(page_num * 100 / actual_max_pages)),
            text=f"Pagina {page_num}/{actual_max_pages} opgehaald ({len(all_results)} listings)...",
        )

    progress_bar.progress(100, text=f"Scraping voltooid! {len(all_results)} listings gevonden.")

    # Trim to max_results
    if len(all_results) > max_results:
        all_results = all_results[:max_results]

    # Convert to flat format for the parser
    parsed = []
    for item in all_results:
        real_estate = item.get("realEstate", item)
        converted = _convert_next_data_to_flat(real_estate)
        if converted:
            parsed.append(converted)

    progress_bar.empty()
    return parsed


def _fetch_search_page(url: str, page: int = 1) -> dict | None:
    """
    Fetch a single search results page and extract the data from __NEXT_DATA__.
    """
    # Add pagination parameter
    page_url = _add_page_param(url, page)

    try:
        resp = requests.get(page_url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        st.warning(f"Fout bij ophalen pagina {page}: {e}")
        return None

    # Extract __NEXT_DATA__ JSON
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        resp.text,
        re.DOTALL,
    )
    if not match:
        return None

    try:
        next_data = json.loads(match.group(1))
        queries = (
            next_data.get("props", {})
            .get("pageProps", {})
            .get("dehydratedState", {})
            .get("queries", [])
        )
        if not queries:
            return None

        # Find the query with search results
        for query in queries:
            data = query.get("state", {}).get("data", {})
            if isinstance(data, dict) and "results" in data:
                return data

        return None
    except (json.JSONDecodeError, KeyError):
        return None


def _clean_search_url(url: str) -> str:
    """
    Clean an Immobiliare.it search URL to ensure server-side rendering.

    Some URLs contain SEO-friendly path segments (like 'con-piani-intermedi',
    'con-ascensore') that trigger client-side rendering instead of SSR.
    We strip these segments while keeping the query parameters that represent
    the same filters.
    """
    parsed = urlparse(url)
    path = parsed.path

    # Known SEO path segments that cause client-side rendering
    seo_segments = {
        "con-piani-intermedi", "con-ascensore", "con-terrazzo",
        "con-balcone", "con-cantina", "con-giardino", "con-piscina",
        "con-arredato", "con-box-auto", "nuove-costruzioni",
        "aste-escluse", "da-ristrutturare", "buono-stato",
        "ultimo-piano", "piano-terra", "piani-alti", "piani-bassi",
    }

    path_parts = path.rstrip("/").split("/")
    cleaned_parts = [p for p in path_parts if p not in seo_segments]
    clean_path = "/".join(cleaned_parts) + "/"

    # Remove params that don't work well with SSR or are map-specific
    params = parse_qs(parsed.query, keep_blank_values=True)
    skip_params = {"mapCenter", "zoom", "idMacroarea"}
    # fasciaPiano in query params gives different (fewer) results than the path
    # segment equivalent; remove it so we get the full result set
    skip_params.update(k for k in params if k.startswith("fasciaPiano"))
    clean_params = {k: v for k, v in params.items() if k not in skip_params}

    clean_query = urlencode(clean_params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, clean_path, "", clean_query, ""))


def _add_page_param(url: str, page: int) -> str:
    """Add or replace the pag= parameter in the URL."""
    if page <= 1:
        return url

    # Remove existing pag parameter
    url = re.sub(r'[&?]pag=\d+', '', url)

    # Add new page parameter
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}pag={page}"


def _convert_next_data_to_flat(real_estate: dict) -> dict | None:
    """
    Convert a __NEXT_DATA__ realEstate object to our internal flat format.
    """
    listing_id = real_estate.get("id", "")
    title = real_estate.get("title", "")

    # Price
    price_obj = real_estate.get("price", {})
    price_value = price_obj.get("value") if isinstance(price_obj, dict) else None

    # Skip listings without a clear price (price ranges like "€159,000 - €219,000")
    if not price_value:
        return None

    properties = real_estate.get("properties", [])
    if not properties:
        return None

    # Use main property or first one
    prop = properties[0]
    for p in properties:
        if p.get("isMain", False):
            prop = p
            break

    # Surface
    surface_raw = prop.get("surface", "")
    surface = 0.0
    if isinstance(surface_raw, str):
        m = re.search(r"[\d.,]+", surface_raw.replace(".", "").replace(",", "."))
        if m:
            try:
                surface = float(m.group())
            except ValueError:
                pass
    elif isinstance(surface_raw, (int, float)):
        surface = float(surface_raw)

    if not price_value or not surface:
        return None

    # Location
    location = prop.get("location", {})
    macrozone = location.get("macrozone", "")
    microzone = location.get("microzone", "")
    zone = microzone or macrozone or ""
    address = location.get("address", "")
    city = location.get("city", "")
    latitude = location.get("latitude")
    longitude = location.get("longitude")

    # Floor
    floor_obj = prop.get("floor", {})
    floor = None
    if isinstance(floor_obj, dict):
        abbr = floor_obj.get("abbreviation", "")
        floor_value = floor_obj.get("value", "").lower()
        if abbr and abbr.isdigit():
            floor = int(abbr)
        elif "terra" in floor_value or "ground" in floor_value or abbr == "T":
            floor = 0

    # Elevator
    has_elevator = prop.get("elevator")
    if has_elevator is None:
        floor_val = floor_obj.get("value", "").lower() if isinstance(floor_obj, dict) else ""
        if "with lift" in floor_val or "con ascensore" in floor_val:
            has_elevator = True
        elif "no lift" in floor_val or "senza ascensore" in floor_val:
            has_elevator = False

    # Rooms & bathrooms
    rooms = _safe_int(prop.get("rooms"))
    bathrooms = _safe_int(prop.get("bathrooms"))
    bedrooms = _safe_int(prop.get("bedRoomsNumber"))

    # Condition
    condition = prop.get("ga4Condition", "")

    # Energy class (not always available in list view)
    energy_class = ""
    energy = prop.get("energy", {})
    if isinstance(energy, dict):
        class_obj = energy.get("class", {})
        if isinstance(class_obj, dict):
            energy_class = class_obj.get("name", "")
        elif isinstance(class_obj, str):
            energy_class = class_obj

    # Images — construct large URLs from photo IDs
    images = []
    # Main photo (has medium/large URLs)
    main_photo = prop.get("photo", {})
    if main_photo:
        urls = main_photo.get("urls", {})
        large = urls.get("large", urls.get("medium", ""))
        if large:
            images.append(large)

    # Additional photos from multimedia
    multimedia = prop.get("multimedia", {})
    for photo in multimedia.get("photos", []):
        photo_id = photo.get("id")
        if photo_id:
            # Construct large URL from photo ID
            large_url = f"https://pwm.im-cdn.it/image/{photo_id}/xxl.jpg"
            if large_url not in images:
                images.append(large_url)
        else:
            urls = photo.get("urls", {})
            img_url = urls.get("large", urls.get("medium", urls.get("small", "")))
            if img_url and img_url not in images:
                images.append(img_url)

    # URL
    listing_url = f"https://www.immobiliare.it/annunci/{listing_id}/" if listing_id else ""

    # Description (not available in list view, only in detail)
    description = prop.get("description", "")

    # Features
    features = prop.get("ga4features", [])
    feature_labels = [f.get("label", "") for f in prop.get("featureList", [])]

    # Listing ID (numeriek) — bruikbaar als proxy voor publicatievolgorde
    numeric_id = None
    if listing_id:
        try:
            numeric_id = int(listing_id)
        except (ValueError, TypeError):
            pass

    return {
        "url": listing_url,
        "listing_id": numeric_id,
        "title": title,
        "price": float(price_value),
        "surface_m2": surface,
        "price_per_m2": round(float(price_value) / surface, 2) if surface > 0 else 0,
        "zone": zone,
        "address": address,
        "city": city,
        "floor": floor,
        "has_elevator": has_elevator,
        "rooms": rooms,
        "bathrooms": bathrooms,
        "bedrooms": bedrooms,
        "condition": condition,
        "energy_class": energy_class,
        "building_year": None,
        "condominium_fees": None,
        "description": description,
        "images": images,
        "latitude": latitude,
        "longitude": longitude,
        "features": features,
        "feature_labels": feature_labels,
    }


def _safe_int(val) -> int | None:
    """Safely convert a value to int."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _run_actor(api_key: str, actor_id: str, run_input: dict) -> list[dict]:
    """
    Start een Apify actor, wacht tot die klaar is, en haalt de resultaten op.
    Used as fallback for single listing URLs.
    """
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
