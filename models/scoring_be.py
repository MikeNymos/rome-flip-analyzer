"""
Flip Score berekening voor Belgische panden.
Gewogen scoresysteem (0-100) met 6 subscores.
"""
from __future__ import annotations

from data.neighborhoods_be import match_neighborhood


def calculate_flip_score_be(listing: dict, analysis: dict, params: dict) -> dict:
    """
    Berekent de Flip Score (0-100) voor een Belgisch pand.

    Subscores:
        Prijs/m² (25%), ROI (25%), Locatie (20%),
        Risico (15%), Liquiditeit (10%), Oppervlakte (5%)

    Returns:
        dict met: flip_score, component_scores, score_explanations,
                  risk_flags, weights
    """
    living_area = listing.get("living_area", listing.get("surface_m2", 80))
    price = listing.get("price", 0)
    price_m2 = price / living_area if living_area > 0 else 0

    arv_data = analysis.get("arv_estimate", {})
    ref_m2 = arv_data.get("ref_price_m2", {}).get("mid", 3000)
    roi = analysis.get("roi", 0)
    arv = analysis.get("arv", 0)
    reno = analysis.get("renovation_estimate", {})

    # === 1. PRIJS PER M² SCORE (25%) ===
    verschil_pct = ((ref_m2 - price_m2) / ref_m2 * 100) if ref_m2 > 0 else 0
    if verschil_pct >= 50:
        price_score = 100
    elif verschil_pct <= 0:
        price_score = 0
    else:
        price_score = round(verschil_pct * 2)

    price_explanation = (
        f"Vraagprijs/m² is €{price_m2:,.0f}, gerenoveerde referentieprijs is €{ref_m2:,.0f}/m². "
        f"Verschil: {verschil_pct:+.0f}%. "
    )
    if verschil_pct > 30:
        price_explanation += "Sterke marge tussen aankoop en verkoopwaarde."
    elif verschil_pct > 15:
        price_explanation += "Voldoende marge voor een flip."
    elif verschil_pct > 0:
        price_explanation += "Krappe marge — weinig ruimte voor tegenvallers."
    else:
        price_explanation += "Vraagprijs ligt boven of gelijk aan gerenoveerde referentieprijs — geen marge."

    # === 2. ROI SCORE (25%) ===
    if roi >= 50:
        roi_score = 100
    elif roi <= 0:
        roi_score = 0
    else:
        roi_score = round((roi / 50) * 100)

    roi_explanation = f"Verwachte ROI: {roi:.1f}% (bruto op BV, vóór VenB). "
    if roi >= 25:
        roi_explanation += "Uitstekend rendement."
    elif roi >= 20:
        roi_explanation += "Goed rendement, boven minimale drempel van 20%."
    elif roi >= 15:
        roi_explanation += "Redelijk maar onder de aanbevolen 20% drempel."
    elif roi > 0:
        roi_explanation += "Marginaal rendement — risico op verlies bij tegenvallers."
    else:
        roi_explanation += "Verlieslatend."

    # === 3. LOCATIE SCORE (20%) ===
    postal_code = listing.get("address_postal_code", listing.get("postal_code", ""))
    municipality = listing.get("address_municipality", "")
    neighborhood = match_neighborhood(postal_code, municipality)

    base_location_score = neighborhood["score"] if neighborhood else 50

    # Micro-locatiefactoren (vereenvoudigd zonder geo-data)
    micro_adj = 0
    location_factors = []

    flood_zone = listing.get("flood_zone", "NON_FLOOD_ZONE")
    if flood_zone == "EFFECTIVE_FLOOD_ZONE":
        micro_adj -= 10
        location_factors.append({"name": "Effectief overstromingsgebied", "impact": -10, "category": "negatief"})
    elif flood_zone == "POSSIBLE_FLOOD_ZONE":
        micro_adj -= 5
        location_factors.append({"name": "Mogelijk overstromingsgebied", "impact": -5, "category": "negatief"})

    location_score = max(0, min(100, base_location_score + micro_adj))
    location_explanation = (
        f"Wijk: {neighborhood['name'] if neighborhood else 'Onbekend'} "
        f"(Tier {neighborhood['tier'] if neighborhood else '?'}). "
        f"Basisscore: {base_location_score}/100."
    )

    # === 4. RISICO SCORE (15%) — hoog = laag risico = goed ===
    risk_score = 60
    risk_flags = []

    level = reno.get("level", "")
    if level == "opfrisbeurt":
        risk_score += 20
    elif level == "zware_renovatie":
        risk_score -= 10
        risk_flags.append("Zware renovatie vereist")

    condition = listing.get("condition", "")
    year = listing.get("construction_year")

    prop_type = listing.get("property_type", "")
    if prop_type in ("APARTMENT", "STUDIO", "DUPLEX", "PENTHOUSE"):
        risk_score += 10

    if year and year > 1990:
        risk_score += 10
    elif year and year < 1950:
        risk_score -= 10
        risk_flags.append(f"Oud gebouw (bouwjaar {year})")

    if flood_zone == "EFFECTIVE_FLOOD_ZONE":
        risk_score -= 30
        risk_flags.append("Effectief overstromingsgebied")
    elif flood_zone == "POSSIBLE_FLOOD_ZONE":
        risk_score -= 15
        risk_flags.append("Mogelijk overstromingsgebied")

    epc = listing.get("epc_score", "")
    if epc in ("F", "G"):
        risk_score -= 10
        risk_flags.append(f"Slechte EPC ({epc})")

    # Beschrijving red flags
    description = listing.get("description", "").lower()
    from data.constants_be import RED_FLAGS_BE
    for keyword, info in RED_FLAGS_BE.items():
        if keyword in description:
            risk_score += info["penalty"]
            risk_flags.append(info["label"])

    risk_score = max(0, min(100, risk_score))
    risk_explanation = f"Risicoscore: {risk_score}/100. {len(risk_flags)} risicovlag(gen) gedetecteerd."

    # === 5. LIQUIDITEIT SCORE (10%) ===
    liq_score = 30
    tier = neighborhood["tier"] if neighborhood else 3

    if tier == 1:
        liq_score += 30
    elif tier == 2:
        liq_score += 20
    elif tier == 3:
        liq_score += 5
    elif tier == 4:
        liq_score -= 10

    if prop_type in ("APARTMENT", "STUDIO") and 60 <= living_area <= 100:
        liq_score += 20

    bedrooms = listing.get("bedroom_count", 0)
    if bedrooms in (2, 3):
        liq_score += 15

    if arv and 200000 <= arv <= 400000:
        liq_score += 15
    elif arv and arv > 600000:
        liq_score -= 10

    has_terrace = listing.get("has_terrace", False)
    has_garden = listing.get("has_garden", False)
    if has_terrace or has_garden:
        liq_score += 10

    parking = listing.get("parking_type", "NONE")
    if parking != "NONE":
        liq_score += 10

    liq_score = max(0, min(100, liq_score))
    liq_explanation = f"Liquiditeitsscore: {liq_score}/100. Tier {tier} wijk."

    # === 6. OPPERVLAKTE SCORE (5%) ===
    if 75 <= living_area <= 120:
        area_score = 95
    elif 60 <= living_area < 75:
        area_score = 80
    elif 120 < living_area <= 180:
        area_score = 70
    elif 40 <= living_area < 60:
        area_score = 50
    elif 180 < living_area <= 250:
        area_score = 40
    elif living_area < 40:
        area_score = 30
    else:
        area_score = 20
    area_explanation = f"Oppervlakte: {living_area:.0f}m². Sweet spot: 75-120m²."

    # === TOTAALSCORE ===
    weights = {
        "price_m2": 0.25,
        "roi": 0.25,
        "location": 0.20,
        "risk": 0.15,
        "liquidity": 0.10,
        "surface": 0.05,
    }

    flip_score = round(
        price_score * weights["price_m2"]
        + roi_score * weights["roi"]
        + location_score * weights["location"]
        + risk_score * weights["risk"]
        + liq_score * weights["liquidity"]
        + area_score * weights["surface"]
    )

    # Automatische uitsluitingen
    if reno.get("is_excluded"):
        risk_flags.insert(0, reno.get("exclusion_reason", "Buiten scope"))
        flip_score = 0

    if living_area < 30:
        risk_flags.insert(0, "Oppervlakte te klein (<30m²) — geen flip-potentieel")
        flip_score = 0

    if roi < 0:
        risk_flags.insert(0, "Verlieslatend")

    min_roi = params.get("min_roi", 0.20) * 100
    if roi < min_roi and roi > 0:
        risk_flags.append(f"Onder minimale ROI-drempel ({min_roi:.0f}%)")

    return {
        "flip_score": max(0, min(100, flip_score)),
        "component_scores": {
            "price_m2": price_score,
            "roi": roi_score,
            "location": location_score,
            "risk": risk_score,
            "liquidity": liq_score,
            "surface": area_score,
        },
        "score_explanations": {
            "price_m2": price_explanation,
            "roi": roi_explanation,
            "location": location_explanation,
            "risk": risk_explanation,
            "liquidity": liq_explanation,
            "surface": area_explanation,
        },
        "risk_flags": risk_flags,
        "weights": weights,
        "location_quality": {
            "overall_score": location_score,
            "factors": location_factors,
            "summary": location_explanation,
            "neighborhood": neighborhood["name"] if neighborhood else "Onbekend",
            "tier": tier,
        },
    }
