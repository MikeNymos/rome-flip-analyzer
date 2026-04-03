"""
Verkoopprijsschatting (ARV) voor Belgische panden.
ARV = Referentieprijs_m2_straatniveau × Oppervlakte × Pandcorrectie_product
"""
from __future__ import annotations

from data.neighborhoods_be import get_reference_price, PROPERTY_TYPE_FACTOR
from data.streets_be import classify_street


def estimate_arv(listing: dict, params: dict) -> dict:
    """
    Schat de After Repair Value (verkoopprijs na renovatie).

    Formule:
        Referentieprijs_m2 = Wijk_basis_m2 × Straatcorrectie × Typecorrectie
        ARV = Referentieprijs_m2 × living_area × Pandcorrectie_product

    Pandcorrectie_product is begrensd op 0.80 tot 1.25.

    Returns:
        dict met: ref_price_m2, street_correction, type_correction,
                  property_corrections[], correction_product, arv,
                  arv_per_m2, neighborhood_name
    """
    living_area = listing.get("living_area", listing.get("surface_m2", 80))
    postal_code = listing.get("address_postal_code", listing.get("postal_code", ""))
    municipality = listing.get("address_municipality", listing.get("municipality", ""))
    street = listing.get("address_street", listing.get("address", ""))
    prop_type = _determine_property_type(listing)

    # 1. Wijkreferentieprijs
    ref = get_reference_price(postal_code, prop_type, municipality)
    base_mid = ref["ref_price_mid"]
    base_low = ref["ref_price_low"]
    base_high = ref["ref_price_high"]

    # 2. Straatcorrectie
    street_info = classify_street(postal_code, street)
    street_factor = street_info["factor"]

    # 3. Typecorrectie
    type_factor = PROPERTY_TYPE_FACTOR.get(prop_type, 1.00)

    # Referentieprijs op straatniveau
    ref_m2_mid = round(base_mid * street_factor * type_factor)
    ref_m2_low = round(base_low * street_factor * type_factor)
    ref_m2_high = round(base_high * street_factor * type_factor)

    # 4. Pandcorrectiefactoren (cumulatief)
    corrections = []
    correction_product = 1.0

    # Terras
    has_terrace = listing.get("has_terrace", False)
    terrace_area = listing.get("terrace_area", 0)
    if has_terrace and terrace_area > 10:
        floor = listing.get("floor")
        factor = 1.10 if (floor is not None and floor >= 3) else 1.07
        correction_product *= factor
        corrections.append({"name": f"Groot terras ({terrace_area}m²)", "factor": factor})
    elif has_terrace:
        correction_product *= 1.02
        corrections.append({"name": "Klein terras", "factor": 1.02})

    # Geen buitenruimte
    has_garden = listing.get("has_garden", False)
    if not has_terrace and not has_garden:
        correction_product *= 0.97
        corrections.append({"name": "Geen terras/tuin", "factor": 0.97})

    # Tuin
    garden_area = listing.get("garden_area", 0)
    if has_garden and garden_area > 30:
        correction_product *= 1.05
        corrections.append({"name": f"Tuin ({garden_area}m²)", "factor": 1.05})

    # Penthouse / bovenste verdieping
    floor = listing.get("floor")
    floor_count = listing.get("floor_count")
    prop_type_raw = listing.get("property_type", "")
    if prop_type_raw == "PENTHOUSE" or (floor and floor_count and floor == floor_count and floor >= 3):
        correction_product *= 1.12
        corrections.append({"name": "Penthouse / bovenste verdieping", "factor": 1.12})

    # Gelijkvloers zonder tuin
    if floor == 0 and not has_garden:
        correction_product *= 0.93
        corrections.append({"name": "Gelijkvloers zonder tuin", "factor": 0.93})

    # Lift
    has_lift = listing.get("has_lift", False)
    if has_lift and floor is not None and floor >= 2:
        correction_product *= 1.03
        corrections.append({"name": "Lift aanwezig", "factor": 1.03})
    elif not has_lift and floor is not None and floor >= 3:
        correction_product *= 0.92
        corrections.append({"name": f"Geen lift + verdieping {floor}", "factor": 0.92})

    # Garage / parking
    parking = listing.get("parking_type", "NONE")
    if parking != "NONE":
        correction_product *= 1.04
        corrections.append({"name": "Garage/parkeerplaats", "factor": 1.04})

    # EPC
    epc = listing.get("epc_score", "")
    if epc in ("A", "B", "C"):
        correction_product *= 1.03
        corrections.append({"name": f"EPC {epc}", "factor": 1.03})
    elif epc in ("E", "F", "G"):
        correction_product *= 0.97
        corrections.append({"name": f"EPC {epc}", "factor": 0.97})

    # Oriëntatie
    orientation = listing.get("orientation", "")
    if orientation in ("S", "SW") and (has_terrace or has_garden):
        correction_product *= 1.02
        corrections.append({"name": f"Oriëntatie {orientation}", "factor": 1.02})
    elif orientation == "N" and (has_terrace or has_garden):
        correction_product *= 0.98
        corrections.append({"name": "Oriëntatie Noord", "factor": 0.98})

    # Slaapkamers > 2
    bedrooms = listing.get("bedroom_count", 0)
    if bedrooms > 2:
        correction_product *= 1.02
        corrections.append({"name": f"{bedrooms} slaapkamers", "factor": 1.02})

    # Duplex/Triplex
    if prop_type_raw in ("DUPLEX", "TRIPLEX"):
        correction_product *= 1.02
        corrections.append({"name": prop_type_raw.capitalize(), "factor": 1.02})

    # Gevelbreedte > 6m (huizen)
    facade_width = listing.get("facade_width")
    if facade_width and facade_width > 6:
        correction_product *= 1.03
        corrections.append({"name": f"Brede gevel ({facade_width}m)", "factor": 1.03})

    # Begrenzing 0.80 – 1.25
    correction_product = max(0.80, min(1.25, correction_product))

    # ARV berekening
    arv_m2_mid = round(ref_m2_mid * correction_product)
    arv_m2_low = round(ref_m2_low * correction_product)
    arv_m2_high = round(ref_m2_high * correction_product)

    arv_mid = round(arv_m2_mid * living_area)
    arv_low = round(arv_m2_low * living_area)
    arv_high = round(arv_m2_high * living_area)

    return {
        "neighborhood_name": ref["neighborhood"],
        "neighborhood_tier": ref["tier"],
        "neighborhood_score": ref["score"],
        "base_price_m2": {"low": base_low, "mid": base_mid, "high": base_high},
        "street_correction": street_info,
        "type_correction": {"type": prop_type, "factor": type_factor},
        "ref_price_m2": {"low": ref_m2_low, "mid": ref_m2_mid, "high": ref_m2_high},
        "property_corrections": corrections,
        "correction_product": round(correction_product, 3),
        "arv_per_m2": {"low": arv_m2_low, "mid": arv_m2_mid, "high": arv_m2_high},
        "arv": {"low": arv_low, "mid": arv_mid, "high": arv_high},
        "living_area": living_area,
    }


def _determine_property_type(listing: dict) -> str:
    """Bepaalt het pandtype voor typecorrectie."""
    ptype = listing.get("property_type", "APARTMENT")
    subtype = listing.get("property_subtype", "")
    facade_count = listing.get("facade_count")

    if ptype == "HOUSE" or ptype in ("VILLA", "MANSION"):
        if facade_count == 4:
            return "HOUSE_DETACHED"
        elif facade_count and facade_count >= 3:
            return "HOUSE_SEMI"
        else:
            return "HOUSE_ROW"

    if ptype in ("PENTHOUSE", "DUPLEX", "TRIPLEX", "STUDIO", "LOFT", "GROUND_FLOOR"):
        return ptype

    return "APARTMENT"
