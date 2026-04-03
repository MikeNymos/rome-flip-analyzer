"""
Immoweb.be scraping module voor Belgische vastgoeddata.
Gebruikt de Apify actor 'azzouzana/immoweb-be-mass-scraper-by-search-url'.
"""
from __future__ import annotations

import re
import json
import time
import requests
import streamlit as st

from data.neighborhoods_be import FOCUS_POSTCODES
from data.constants_be import CONDITION_MAP_BE

APIFY_BASE_URL = "https://api.apify.com/v2"
IMMOWEB_ACTOR_ID = "azzouzana~immoweb-be-mass-scraper-by-search-url"


def run_immoweb_scraper(api_key: str, url: str, max_results: int = 100) -> list[dict]:
    """
    Scrapt Immoweb listings via Apify actor.

    Args:
        api_key: Apify API key.
        url: Immoweb zoek-URL (bv. https://www.immoweb.be/nl/zoeken/appartement/te-koop/antwerpen/2018)
        max_results: Maximum aantal resultaten.

    Returns:
        Lijst van genormaliseerde listing dicts.
    """
    if not api_key:
        raise ValueError("Apify API key is vereist voor Immoweb scraping.")

    if not validate_immoweb_url(url):
        raise ValueError("Ongeldige Immoweb URL. Verwacht: https://www.immoweb.be/nl/zoeken/...")

    run_input = {
        "startUrl": url,
        "maxItems": max_results,
    }

    # Start actor run
    try:
        resp = requests.post(
            f"{APIFY_BASE_URL}/acts/{IMMOWEB_ACTOR_ID}/runs",
            params={"token": api_key},
            json=run_input,
            timeout=30,
        )
        resp.raise_for_status()
        run_data = resp.json()["data"]
        run_id = run_data["id"]
        dataset_id = run_data["defaultDatasetId"]
    except requests.RequestException as e:
        raise Exception(f"Kon Apify actor niet starten: {e}")

    # Poll voor resultaten
    progress = st.progress(0, text="Immoweb scraper draait...")
    for i in range(120):  # max 10 minuten
        try:
            status_resp = requests.get(
                f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                params={"token": api_key},
                timeout=15,
            )
            status_resp.raise_for_status()
            status = status_resp.json()["data"]["status"]
        except requests.RequestException:
            time.sleep(5)
            continue

        if status == "SUCCEEDED":
            progress.progress(100, text="Scraping voltooid!")
            break
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            progress.empty()
            raise Exception(f"Apify scraper mislukt: {status}")

        progress.progress(
            min(95, int((i / 120) * 100)),
            text=f"Immoweb scraper draait... ({status})",
        )
        time.sleep(5)
    else:
        progress.empty()
        raise Exception("Scraping timeout na 10 minuten.")

    # Haal resultaten op
    try:
        results_resp = requests.get(
            f"{APIFY_BASE_URL}/datasets/{dataset_id}/items",
            params={"token": api_key, "format": "json"},
            timeout=60,
        )
        results_resp.raise_for_status()
        raw_items = results_resp.json()
    except requests.RequestException as e:
        progress.empty()
        raise Exception(f"Kon resultaten niet ophalen: {e}")

    progress.empty()

    if not raw_items:
        st.warning("Geen resultaten gevonden van Immoweb.")
        return []

    # Normaliseer items
    listings = []
    for item in raw_items:
        normalized = _normalize_immoweb_item(item)
        if normalized:
            listings.append(normalized)

    return listings


def _normalize_immoweb_item(raw: dict) -> dict | None:
    """
    Normaliseert een Immoweb listing naar het interne formaat.
    Extraheert alle 35 velden uit de specificatie.
    """
    # Probeer genest formaat (window.classified) of plat formaat
    prop = raw.get("property", raw)
    price_obj = raw.get("price", {})
    transaction = raw.get("transaction", {})
    location = prop.get("location", {})
    building = prop.get("building", {})

    # Prijs — verplicht
    price = price_obj.get("mainValue") if isinstance(price_obj, dict) else raw.get("price")
    if not price:
        price = raw.get("Price") or raw.get("askingPrice")
    if not price:
        return None
    try:
        price = float(str(price).replace(".", "").replace(",", ".").replace("€", "").strip())
    except (ValueError, TypeError):
        return None

    # Oppervlakte — verplicht
    living_area = (
        prop.get("netHabitableSurface")
        or prop.get("surfaceTotal")
        or raw.get("livingArea")
        or raw.get("LivingArea")
        or raw.get("surface")
    )
    if not living_area:
        return None
    try:
        living_area = float(living_area)
    except (ValueError, TypeError):
        return None

    if living_area <= 0 or price <= 0:
        return None

    # Postcode — verplicht
    postal_code = str(
        location.get("postalCode")
        or raw.get("postalCode")
        or raw.get("PostalCode")
        or ""
    ).strip()
    if not postal_code:
        return None

    # Locatie
    municipality = location.get("locality") or raw.get("locality") or raw.get("Municipality") or ""
    street = location.get("street") or raw.get("street") or raw.get("Street") or ""
    latitude = location.get("latitude") or raw.get("latitude")
    longitude = location.get("longitude") or raw.get("longitude")

    # Type pand
    prop_type = prop.get("type") or raw.get("propertyType") or raw.get("Type") or "APARTMENT"
    prop_subtype = prop.get("subtype") or raw.get("propertySubType") or ""

    # Staat
    condition = building.get("condition") or raw.get("condition") or raw.get("Condition") or "TO_BE_DONE_UP"

    # Gebouw details
    construction_year = building.get("constructionYear") or raw.get("constructionYear")
    if construction_year:
        try:
            construction_year = int(construction_year)
        except (ValueError, TypeError):
            construction_year = None

    floor = location.get("floor") or raw.get("floor")
    if floor is not None:
        try:
            floor = int(floor)
        except (ValueError, TypeError):
            floor = None

    floor_count = building.get("floorCount") or raw.get("floorCount")
    if floor_count:
        try:
            floor_count = int(floor_count)
        except (ValueError, TypeError):
            floor_count = None

    has_lift = building.get("hasLift") or raw.get("hasLift") or False
    bedroom_count = prop.get("bedroomCount") or raw.get("bedroomCount") or 0
    bathroom_count = prop.get("bathroomCount") or raw.get("bathroomCount") or 1

    # Buitenruimte
    has_terrace = prop.get("hasTerrace") or raw.get("hasTerrace") or False
    terrace_area = prop.get("terraceSurface") or raw.get("terraceSurface") or 0
    has_garden = prop.get("hasGarden") or raw.get("hasGarden") or False
    garden_area = prop.get("gardenSurface") or raw.get("gardenSurface") or 0

    # Parking
    parking_indoor = prop.get("parkingCountIndoor") or raw.get("parkingCountIndoor") or 0
    parking_outdoor = prop.get("parkingCountOutdoor") or raw.get("parkingCountOutdoor") or 0
    parking_count = int(parking_indoor or 0) + int(parking_outdoor or 0)
    if parking_indoor and int(parking_indoor) > 0:
        parking_type = "INDOOR_PARKING"
    elif parking_outdoor and int(parking_outdoor) > 0:
        parking_type = "OUTDOOR_PARKING"
    else:
        parking_type = "NONE"

    has_basement = prop.get("hasBasement") or raw.get("hasBasement") or False

    # EPC
    certs = transaction.get("certificates", raw.get("certificates", {}))
    if isinstance(certs, dict):
        epc_score = certs.get("epcScore") or raw.get("epcScore") or ""
        epc_value = certs.get("primaryEnergyConsumptionPerSqm") or raw.get("primaryEnergyConsumptionPerSqm")
    else:
        epc_score = raw.get("epcScore", "")
        epc_value = raw.get("primaryEnergyConsumptionPerSqm")

    if epc_value:
        try:
            epc_value = float(epc_value)
        except (ValueError, TypeError):
            epc_value = None

    # Overige velden
    orientation = prop.get("orientation") or raw.get("orientation") or ""
    cadastral_income = (
        transaction.get("sale", {}).get("cadastralIncome")
        if isinstance(transaction.get("sale"), dict) else None
    ) or raw.get("cadastralIncome")

    flood_zone = (
        prop.get("flooding", {}).get("floodZoneType")
        if isinstance(prop.get("flooding"), dict) else None
    ) or raw.get("floodZoneType") or "NON_FLOOD_ZONE"

    facade_count = building.get("facadeCount") or raw.get("facadeCount")
    facade_width = building.get("facadeWidth") or raw.get("facadeWidth")

    description = prop.get("description") or raw.get("description") or ""

    # Foto's
    photos = []
    media = raw.get("media", {})
    if isinstance(media, dict):
        for pic in media.get("pictures", []):
            url = pic.get("url") or pic.get("mediumUrl") or ""
            if url:
                photos.append(url)
    if not photos:
        # Probeer plat formaat
        for key in ("imageUrl", "ImageUrl", "mainImage", "pictureUrl"):
            if raw.get(key):
                photos.append(raw[key])
                break

    # URL
    listing_url = raw.get("url") or raw.get("Url") or raw.get("classifiedUrl") or ""

    # Publicatiedatum
    pub = raw.get("publication", {})
    pub_date = (
        pub.get("creationDate") if isinstance(pub, dict) else None
    ) or raw.get("publicationDate") or ""

    # Makelaar
    customers = raw.get("customers", [])
    agent_name = customers[0].get("name", "Onbekend") if customers else "Onbekend"

    # Heritage check
    is_heritage = False
    desc_lower = description.lower()
    for kw in ("beschermd", "monument", "erfgoed", "patrimoine"):
        if kw in desc_lower:
            is_heritage = True
            break

    # Renovatieniveau
    renovation_level = CONDITION_MAP_BE.get(condition, "lichte_renovatie")

    # Check scope
    is_in_scope = (
        postal_code in FOCUS_POSTCODES
        and condition != "TO_RESTORE"
        and not is_heritage
    )

    return {
        "price": price,
        "living_area": living_area,
        "surface_m2": living_area,  # alias voor compatibiliteit
        "price_per_sqm": round(price / living_area, 2),
        "price_per_m2": round(price / living_area, 2),  # alias
        "address_street": street,
        "address": street,  # alias
        "address_postal_code": postal_code,
        "postal_code": postal_code,  # alias
        "address_municipality": municipality,
        "municipality": municipality,  # alias
        "zone": f"{municipality} ({postal_code})" if municipality else postal_code,
        "property_type": prop_type.upper() if prop_type else "APARTMENT",
        "property_subtype": prop_subtype,
        "condition": condition,
        "construction_year": construction_year,
        "floor": floor,
        "floor_count": floor_count,
        "has_lift": bool(has_lift),
        "bedroom_count": int(bedroom_count or 0),
        "bathroom_count": int(bathroom_count or 1),
        "has_terrace": bool(has_terrace),
        "terrace_area": float(terrace_area or 0),
        "has_garden": bool(has_garden),
        "garden_area": float(garden_area or 0),
        "parking_type": parking_type,
        "parking_count": parking_count,
        "has_basement": bool(has_basement),
        "epc_score": str(epc_score).upper() if epc_score else "",
        "epc_value": epc_value,
        "orientation": orientation,
        "cadastral_income": cadastral_income,
        "flood_zone": flood_zone,
        "facade_count": int(facade_count) if facade_count else None,
        "facade_width": float(facade_width) if facade_width else None,
        "description": description,
        "images": photos,
        "photos": photos,  # alias
        "url": listing_url,
        "publication_date": pub_date,
        "agent_name": agent_name,
        "is_heritage": is_heritage,
        "renovation_level": renovation_level,
        "is_in_scope": is_in_scope,
        "latitude": latitude,
        "longitude": longitude,
        "country": "BE",
    }


def validate_immoweb_url(url: str) -> bool:
    """Controleert of een URL een geldige Immoweb zoek-URL is."""
    url = url.strip().lower()
    return "immoweb.be" in url
