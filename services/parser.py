"""
Listing data parser & normalizer.
Parseert data van Apify, JSON, CSV en XLSX naar een uniform intern datamodel.

Ondersteunt twee Apify output-structuren:
1. azzouzana actor: genest formaat met properties[], price.value, location.macrozone etc.
2. Eenvoudig/plat formaat: directe velden zoals price, surface_m2, zone etc.
"""
from __future__ import annotations

import json
import io
import re
import pandas as pd
from utils.helpers import safe_float, safe_int


def normalize_apify_item(raw: dict) -> list[dict]:
    """
    Normaliseert een enkel Apify-resultaat van de azzouzana actor.

    Deze actor retourneert items met een geneste structuur:
    - price.value: prijs
    - properties[]: lijst van sub-properties (elk een aparte woning)
    - properties[i].location: locatiedetails
    - properties[i].surface: oppervlakte als string ("128 m²")
    - properties[i].floor.abbreviation: verdiepingsnummer
    - properties[i].elevator: boolean
    - properties[i].rooms: kamers als string ("3 - 4" of "3")
    - properties[i].bathrooms: badkamers als string
    - properties[i].description: beschrijving
    - properties[i].energy.class.name: energieklasse

    Eén Apify-item kan meerdere properties bevatten (bv. bij nieuwbouwprojecten).
    We retourneren een listing per property met isMain=True, of alle als er geen main is.
    """
    properties = raw.get("properties", [])
    if not properties:
        # Geen geneste structuur -> probeer plat formaat
        return [normalize_listing(raw)]

    # Top-level prijs (soms per property, soms top-level)
    top_price = None
    price_obj = raw.get("price", {})
    if isinstance(price_obj, dict):
        top_price = safe_float(price_obj.get("value"))
    elif isinstance(price_obj, (int, float)):
        top_price = float(price_obj)

    # Bouw URL
    item_id = raw.get("id", "")
    input_url = raw.get("iput_url", raw.get("input_url", ""))
    if not input_url and item_id:
        input_url = f"https://www.immobiliare.it/annunci/{item_id}/"

    results = []
    for prop in properties:
        # Sla sub-properties over die geen hoofdwoning zijn (bij projecten)
        # tenzij er maar 1 property is
        if len(properties) > 1 and not prop.get("isMain", False):
            continue

        listing = _parse_property(prop, top_price, input_url)
        if listing:
            results.append(listing)

    # Als geen isMain gevonden, neem de eerste
    if not results and properties:
        listing = _parse_property(properties[0], top_price, input_url)
        if listing:
            results.append(listing)

    return results


def _parse_property(prop: dict, top_price: float | None, input_url: str) -> dict | None:
    """Parseert een enkel property-object uit de Apify output."""

    # Prijs: property-level of top-level
    price_obj = prop.get("price", {})
    if isinstance(price_obj, dict):
        price = safe_float(price_obj.get("value"))
    elif isinstance(price_obj, (int, float)):
        price = float(price_obj)
    else:
        price = 0
    if not price and top_price:
        price = top_price

    # Oppervlakte: string "128 m²" -> float
    surface_raw = prop.get("surface", "")
    surface = _parse_surface(surface_raw)

    if not price or not surface:
        return None

    # Locatie
    location = prop.get("location", {})
    zone = location.get("macrozone", "") or location.get("microzone", "") or ""
    city = location.get("city", "")
    address = location.get("address", "")
    if not zone and address:
        zone = _extract_zone_from_address(address)

    # Verdieping
    floor_obj = prop.get("floor", {})
    if isinstance(floor_obj, dict):
        floor_abbr = floor_obj.get("abbreviation", "")
        floor = safe_int(floor_abbr)
        # Check "piano terra" / "T" = begane grond
        floor_value = floor_obj.get("value", "").lower()
        if "terra" in floor_value or floor_abbr == "T":
            floor = 0
    else:
        floor = safe_int(floor_obj)

    # Lift
    has_elevator = prop.get("elevator")
    if has_elevator is None:
        # Check in floor value string
        floor_val = ""
        if isinstance(floor_obj, dict):
            floor_val = floor_obj.get("value", "").lower()
        if "ascensore" in floor_val or "con ascensore" in floor_val:
            has_elevator = True
        elif "senza ascensore" in floor_val:
            has_elevator = False

    # Kamers & badkamers
    rooms_raw = prop.get("rooms", "")
    rooms = _parse_rooms(rooms_raw)
    bathrooms = safe_int(prop.get("bathrooms", prop.get("bathroomsNumber")))

    # Beschrijving
    description = prop.get("description", prop.get("defaultDescription", ""))
    caption = prop.get("caption", "")
    title = caption if caption else f"Appartamento {zone} {city}".strip()

    # Energie
    energy = prop.get("energy", {})
    energy_class = ""
    if isinstance(energy, dict):
        class_obj = energy.get("class", {})
        if isinstance(class_obj, dict):
            energy_class = class_obj.get("name", "")
        elif isinstance(class_obj, str):
            energy_class = class_obj

    # Conditie
    condition = prop.get("condition", "")
    typology_value = prop.get("typologyValue", "")

    # Condominium kosten
    costs = prop.get("costs", {})
    condo_fees = None  # Niet altijd beschikbaar in deze actor

    # Afbeeldingen
    multimedia = prop.get("multimedia", {})
    photos = multimedia.get("photos", [])
    images = []
    for photo in photos:
        urls = photo.get("urls", {})
        large = urls.get("large", urls.get("medium", ""))
        if large:
            images.append(large)

    # URL
    prop_id = prop.get("id", "")
    url = input_url
    if prop_id and not url:
        url = f"https://www.immobiliare.it/annunci/{prop_id}/"

    return {
        "url": str(url),
        "title": str(title),
        "price": price,
        "surface_m2": surface,
        "price_per_m2": round(price / surface, 2) if surface > 0 else 0,
        "zone": str(zone),
        "address": str(address),
        "floor": floor,
        "has_elevator": has_elevator,
        "rooms": rooms,
        "bathrooms": bathrooms,
        "condition": str(condition),
        "energy_class": str(energy_class),
        "building_year": None,
        "condominium_fees": condo_fees,
        "description": str(description),
        "images": images,
    }


def _parse_surface(surface_raw) -> float:
    """Parseert oppervlakte uit string of getal. Bv. '128 m²' -> 128.0"""
    if isinstance(surface_raw, (int, float)):
        return float(surface_raw)
    if isinstance(surface_raw, str):
        # Extract getal uit string
        match = re.search(r"[\d.,]+", surface_raw.replace(".", "").replace(",", "."))
        if match:
            return safe_float(match.group())
    return 0.0


def _parse_rooms(rooms_raw) -> int | None:
    """Parseert kamers uit string of getal. Bv. '3 - 4' -> 3, '3' -> 3"""
    if isinstance(rooms_raw, (int, float)):
        return int(rooms_raw)
    if isinstance(rooms_raw, str):
        # Neem het eerste getal
        match = re.search(r"\d+", rooms_raw)
        if match:
            return int(match.group())
    return None


def normalize_listing(raw: dict) -> dict:
    """
    Normaliseert een ruwe listing-dict (plat formaat, van upload of eenvoudige JSON)
    naar het interne model. Probeert meerdere veldnamen.
    """
    def get_field(keys: list, default=None):
        for key in keys:
            val = raw.get(key)
            if val is not None and val != "":
                return val
        return default

    # Check of dit een azzouzana-achtig genest item is
    if "properties" in raw and isinstance(raw.get("properties"), list):
        results = normalize_apify_item(raw)
        return results[0] if results else _empty_listing()

    # Basisvelden
    url = get_field(["url", "link", "detailUrl", "detail_url", "listing_url", "iput_url"], "")
    title = get_field(["title", "titolo", "nome", "name", "caption", "anchor"], "Onbekend pand")
    price = safe_float(get_field(["price_value", "price", "prezzo", "Price", "asking_price"]))
    surface = safe_float(get_field([
        "surface_m2", "surface", "superficie", "size", "mq",
        "squareMeters", "square_meters", "area",
    ]))
    if isinstance(surface, str) or (isinstance(surface, float) and surface == 0):
        surface = _parse_surface(get_field([
            "surface_m2", "surface", "superficie", "size", "mq",
        ], "0"))

    price_per_m2 = price / surface if surface > 0 else 0

    # Locatie
    zone = get_field([
        "zone", "zona", "neighborhood", "quarter", "quartiere",
        "location", "area_name", "district", "macro_zone", "macroZone",
        "macrozone",
    ], "")
    address = get_field(["address", "indirizzo", "full_address", "addr"], "")
    if not zone and address:
        zone = _extract_zone_from_address(address)

    # Verdieping — shahidirfan geeft floor_number als string ("4", "ground floor")
    floor_number_raw = get_field(["floor_number"], "")
    floor_raw = get_field(["floor", "piano", "floorNumber"], "")
    if floor_number_raw:
        if "ground" in str(floor_number_raw).lower() or "terra" in str(floor_number_raw).lower():
            floor = 0
        else:
            floor = safe_int(floor_number_raw)
    else:
        floor = safe_int(floor_raw)

    # Lift detectie — check meerdere bronnen
    has_elevator = get_field(["has_elevator", "elevator", "ascensore", "hasElevator"])
    if isinstance(has_elevator, str):
        has_elevator = has_elevator.lower() in ["true", "yes", "si", "1", "presente"]
    elif isinstance(has_elevator, (int, float)):
        has_elevator = bool(has_elevator)

    # Check floor string en feature_labels voor lift info
    if has_elevator is None:
        floor_str = str(get_field(["floor"], "")).lower()
        if "with lift" in floor_str or "con ascensore" in floor_str:
            has_elevator = True
        elif "no lift" in floor_str or "senza ascensore" in floor_str:
            has_elevator = False

    if has_elevator is None:
        feature_labels = get_field(["feature_labels"], [])
        if isinstance(feature_labels, list):
            labels_lower = [str(l).lower() for l in feature_labels]
            if any("lift" in l or "ascensore" in l for l in labels_lower):
                has_elevator = True
            elif any("no lift" in l or "senza ascensore" in l for l in labels_lower):
                has_elevator = False

    rooms = safe_int(get_field(["rooms", "locali", "stanze", "numRooms", "num_rooms"]))
    bathrooms = safe_int(get_field(["bathrooms", "bagni", "numBathrooms", "num_bathrooms"]))
    condition = get_field(["condition", "stato", "condizione", "state", "propertyCondition"], "")
    energy_class = get_field([
        "energy_class", "energyClass", "classe_energetica", "classeEnergetica", "ape",
    ], "")
    building_year = safe_int(get_field(["building_year", "anno_costruzione", "buildYear", "year"]))
    condominium_fees = safe_float(get_field([
        "condominium_fees", "spese_condominiali", "condominiumFees",
        "monthlyFee", "speseCondominio",
    ]))
    description = get_field(["description", "descrizione", "text", "body"], "")
    images = get_field(["images", "photos", "foto", "immagini", "imageUrls"], [])
    if isinstance(images, str):
        images = [images]

    return {
        "url": str(url),
        "title": str(title),
        "price": price,
        "surface_m2": surface,
        "price_per_m2": round(price_per_m2, 2),
        "zone": str(zone),
        "address": str(address),
        "floor": floor,
        "has_elevator": has_elevator,
        "rooms": rooms,
        "bathrooms": bathrooms,
        "condition": str(condition),
        "energy_class": str(energy_class) if energy_class else "",
        "building_year": building_year,
        "condominium_fees": condominium_fees,
        "description": str(description),
        "images": images if isinstance(images, list) else [],
    }


def _empty_listing() -> dict:
    """Retourneert een leeg listing-dict."""
    return {
        "url": "", "title": "Onbekend", "price": 0, "surface_m2": 0,
        "price_per_m2": 0, "zone": "", "address": "", "floor": None,
        "has_elevator": None, "rooms": None, "bathrooms": None,
        "condition": "", "energy_class": "", "building_year": None,
        "condominium_fees": None, "description": "", "images": [],
    }


def _extract_zone_from_address(address: str) -> str:
    """Probeert een wijknaam te extraheren uit een adres-string."""
    known_zones = [
        "Prati", "Trieste", "Parioli", "Flaminio", "Centro Storico",
        "Mazzini", "Salario", "Pinciano", "Nomentano", "Trastevere",
        "Testaccio", "Monteverde", "EUR", "San Giovanni", "Appio",
    ]
    address_lower = address.lower()
    for zone in known_zones:
        if zone.lower() in address_lower:
            return zone
    return ""


def parse_json_data(json_data: str | list) -> list[dict]:
    """Parseert JSON data (string of lijst) naar genormaliseerde listings."""
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    if isinstance(data, dict):
        data = [data]

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        # Check of het een azzouzana genest formaat is
        if "properties" in item and isinstance(item.get("properties"), list):
            results.extend(normalize_apify_item(item))
        else:
            results.append(normalize_listing(item))

    return results


def parse_csv_data(csv_content: bytes | str) -> list[dict]:
    """Parseert CSV data naar genormaliseerde listings."""
    if isinstance(csv_content, bytes):
        csv_content = csv_content.decode("utf-8")
    df = pd.read_csv(io.StringIO(csv_content))
    return _parse_dataframe(df)


def parse_xlsx_data(xlsx_content: bytes) -> list[dict]:
    """Parseert Excel data naar genormaliseerde listings."""
    df = pd.read_excel(io.BytesIO(xlsx_content), engine="openpyxl")
    return _parse_dataframe(df)


def _parse_dataframe(df: pd.DataFrame) -> list[dict]:
    """Converteert een DataFrame naar genormaliseerde listings."""
    listings = []
    for _, row in df.iterrows():
        raw = row.to_dict()
        raw = {k: (None if pd.isna(v) else v) for k, v in raw.items()}
        listings.append(normalize_listing(raw))
    return listings


def parse_uploaded_file(file_obj) -> list[dict]:
    """
    Parseert een geüpload bestand (Streamlit UploadedFile) naar listings.
    Ondersteunt: .json, .csv, .xlsx
    """
    filename = file_obj.name.lower()
    content = file_obj.read()

    if filename.endswith(".json"):
        return parse_json_data(content.decode("utf-8"))
    elif filename.endswith(".csv"):
        return parse_csv_data(content)
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        return parse_xlsx_data(content)
    else:
        raise ValueError(f"Onbekend bestandsformaat: {filename}. Ondersteund: .json, .csv, .xlsx")


def filter_valid_listings(listings: list[dict]) -> list[dict]:
    """Filtert listings op minimale datakwaliteit."""
    return [l for l in listings if l["price"] > 0 and l["surface_m2"] > 0]
