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

    # Check voor rate-limit of foutmeldingen van de actor
    if len(raw_items) == 1 and isinstance(raw_items[0], dict) and "message" in raw_items[0]:
        msg = raw_items[0]["message"]
        if "rate limit" in msg.lower() or "limit" in msg.lower():
            raise Exception(
                f"Apify rate-limit: {msg}\n\n"
                "De gratis Apify versie staat slechts 1 run per 30 minuten toe voor deze actor. "
                "Wacht 20-30 minuten en probeer opnieuw, of upgrade naar een betaald Apify-plan."
            )
        raise Exception(f"Actor fout: {msg}")

    # Normaliseer items
    listings = []
    skipped = 0
    for item in raw_items:
        normalized = _normalize_immoweb_item(item)
        if normalized:
            listings.append(normalized)
        else:
            skipped += 1

    if skipped > 0 and not listings:
        st.warning(
            f"Alle {skipped} listings konden niet worden genormaliseerd. "
            "Mogelijk is het dataformaat gewijzigd."
        )
    elif skipped > 0:
        st.caption(f"{skipped} listings overgeslagen (onvolledige data).")

    return listings


def _normalize_immoweb_item(raw: dict) -> dict | None:
    """
    Normaliseert een Immoweb listing (van azzouzana actor) naar intern formaat.

    Actor output structuur (gecontroleerd april 2026):
        transaction.sale.price → prijs
        property.livingDescription.netHabitableSurface → oppervlakte
        property.location.address.postalCode → postcode
        property.building.condition → staat
        transaction.certificates.epc.score → EPC
        media.pictures → foto URLs (dict met URLs als values)
    """
    prop = raw.get("property", {})
    transaction = raw.get("transaction", {})
    building = prop.get("building", {})
    location = prop.get("location", {})
    address = location.get("address", {}) if isinstance(location, dict) else {}

    # === PRIJS (verplicht) ===
    sale = transaction.get("sale", {}) if isinstance(transaction, dict) else {}
    price = sale.get("price") if isinstance(sale, dict) else None
    if not price:
        # Fallback: platte structuur
        price = raw.get("price") or raw.get("Price")
    if not price:
        return None
    try:
        price = float(price)
    except (ValueError, TypeError):
        return None

    # === OPPERVLAKTE (verplicht) ===
    living_desc = prop.get("livingDescription", {})
    living_area = (
        living_desc.get("netHabitableSurface")
        if isinstance(living_desc, dict) else None
    )
    if not living_area:
        living_area = prop.get("netHabitableSurface") or raw.get("livingArea") or raw.get("surface")
    if not living_area:
        return None
    try:
        living_area = float(living_area)
    except (ValueError, TypeError):
        return None
    if living_area <= 0 or price <= 0:
        return None

    # === POSTCODE (verplicht) ===
    postal_code = str(address.get("postalCode") or raw.get("postalCode") or "").strip()
    if not postal_code:
        return None

    # === LOCATIE ===
    municipality = address.get("locality") or address.get("district") or ""
    street = address.get("street") or ""
    street_number = address.get("number") or ""
    if street and street_number:
        street = f"{street} {street_number}"
    floor_raw = address.get("floor")
    latitude = location.get("latitude") or raw.get("latitude")
    longitude = location.get("longitude") or raw.get("longitude")

    # === TYPE PAND ===
    prop_type = prop.get("type") or raw.get("type") or "APARTMENT"
    prop_subtype = prop.get("subtype") or ""

    # === STAAT ===
    condition = building.get("condition") or raw.get("condition") or "TO_BE_DONE_UP"

    # === GEBOUW ===
    construction_year = building.get("constructionYear")
    if construction_year:
        try:
            construction_year = int(construction_year)
        except (ValueError, TypeError):
            construction_year = None

    floor = None
    if floor_raw is not None:
        try:
            floor = int(floor_raw)
        except (ValueError, TypeError):
            pass

    floor_count = building.get("floorCount")
    if floor_count:
        try:
            floor_count = int(floor_count)
        except (ValueError, TypeError):
            floor_count = None

    # Lift: in commonEquipment of building
    common_eq = prop.get("commonEquipment", {})
    has_lift = (
        common_eq.get("hasLift")
        if isinstance(common_eq, dict) else None
    ) or building.get("hasLift") or False

    # Slaapkamers/badkamers
    bedroom = prop.get("bedroom", {})
    bedroom_count = bedroom.get("count") if isinstance(bedroom, dict) else 0
    bathroom = prop.get("bathroom", {})
    bathroom_count = bathroom.get("count") if isinstance(bathroom, dict) else 1

    # === BUITENRUIMTE ===
    outdoor = prop.get("outdoor", {})
    terrace = outdoor.get("terrace", {}) if isinstance(outdoor, dict) else {}
    has_terrace = terrace.get("exists", False) if isinstance(terrace, dict) else False
    terrace_area = terrace.get("surface", 0) if isinstance(terrace, dict) else 0

    garden = outdoor.get("garden", {}) if isinstance(outdoor, dict) else {}
    has_garden = garden.get("exists", False) if isinstance(garden, dict) else False
    garden_area = garden.get("surface", 0) if isinstance(garden, dict) else 0

    # === PARKING ===
    parking = prop.get("parking", {})
    parking_counts = parking.get("parkingSpaceCount", {}) if isinstance(parking, dict) else {}
    parking_total = parking_counts.get("total", 0) if isinstance(parking_counts, dict) else 0
    parking_type = "INDOOR_PARKING" if parking_total and int(parking_total) > 0 else "NONE"

    # === KELDER ===
    basement = prop.get("basementExists") or prop.get("basement", {})
    has_basement = False
    if isinstance(basement, dict):
        has_basement = basement.get("exists", False)
    elif isinstance(basement, bool):
        has_basement = basement

    # === EPC ===
    certs = transaction.get("certificates", {})
    epc_obj = certs.get("epc", {}) if isinstance(certs, dict) else {}
    epc_score = epc_obj.get("score", "") if isinstance(epc_obj, dict) else ""
    energy_cons = certs.get("primaryEnergyConsumption", {}) if isinstance(certs, dict) else {}
    epc_value = energy_cons.get("perSqm") if isinstance(energy_cons, dict) else None
    if epc_value:
        try:
            epc_value = float(epc_value)
        except (ValueError, TypeError):
            epc_value = None

    # === OVERIG ===
    orientation = prop.get("orientation") or ""
    cadastral_income = sale.get("cadastralIncome") if isinstance(sale, dict) else None

    # Overstromingszone
    construction_permit = prop.get("constructionPermit", {})
    flood_zone = (
        construction_permit.get("floodZoneType")
        if isinstance(construction_permit, dict) else "NON_FLOOD_ZONE"
    ) or "NON_FLOOD_ZONE"

    facade_count = building.get("facadeCount")
    facade_width = building.get("streetFacadeWidth") or building.get("facadeWidth")

    description = prop.get("description") or raw.get("description") or ""

    # === FOTO'S ===
    photos = []
    media = raw.get("media", {})
    if isinstance(media, dict):
        pics = media.get("pictures", {})
        if isinstance(pics, dict):
            # Dict formaat: {hash: url_string}
            for key, val in pics.items():
                if isinstance(val, str) and val.startswith("http"):
                    photos.append(val)
        elif isinstance(pics, list):
            for pic in pics:
                if isinstance(pic, str):
                    photos.append(pic)
                elif isinstance(pic, dict):
                    url = pic.get("url") or pic.get("mediumUrl") or ""
                    if url:
                        photos.append(url)

    # === URL ===
    listing_url = raw.get("SEOUrl") or raw.get("url") or raw.get("classifiedUrl") or ""
    listing_id = raw.get("id")

    # === PUBLICATIE ===
    pub = raw.get("publication", {})
    pub_date = pub.get("activationDate", "") if isinstance(pub, dict) else ""

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
        "parking_count": int(parking_total or 0),
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
