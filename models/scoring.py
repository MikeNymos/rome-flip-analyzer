"""
Flip Score berekening (0-100) op basis van gewogen componenten.
Inclusief diepgaande Nederlandse narratieven per component (3-5 zinnen).
"""
from __future__ import annotations

from data.neighborhoods import get_neighborhood_benchmarks
from data.constants import RED_FLAGS
from services.feature_extractor import is_premium_street


def calculate_flip_score(listing: dict, analysis: dict, params: dict) -> dict:
    """
    Berekent een gewogen Flip Score van 0-100 met diepgaande toelichtingen.

    Componenten en gewichten:
    - ROI Score (35%):        Hoe hoger de verwachte ROI, hoe beter
    - Marge Score (20%):      Spread tussen aankoop/m2 en gerenoveerd/m2
    - Locatie Score (15%):    Multi-factor locatieanalyse
    - Risico Score (15%):     Afwezigheid van risicofactoren
    - Liquiditeit Score (10%): Verkoopbaarheid na renovatie
    - Oppervlakte Score (5%):  Sweet spot 100-150m2
    """
    scores: dict[str, int] = {}
    explanations: dict[str, str] = {}
    neighborhood = analysis.get("neighborhood_data", get_neighborhood_benchmarks(listing.get("zone", "")))
    location_quality = analysis.get("location_quality", {})
    sale_estimate = analysis.get("sale_price_estimate", {})
    features = listing.get("features", {})
    zone_name = neighborhood.get("matched_zone", listing.get("zone", "Onbekend"))

    # ═══════════════════════════════════════════════════════
    # 1. ROI SCORE (35%)
    # ═══════════════════════════════════════════════════════
    midpoint_roi = analysis["midpoint_roi"]
    prima = analysis.get("prima_casa", analysis.get("optimistic", {}))
    seconda = analysis.get("seconda_casa", analysis.get("conservative", {}))
    prima_roi = prima.get("roi", 0)
    seconda_roi = seconda.get("roi", 0)

    if midpoint_roi >= 30: scores["roi"] = 100
    elif midpoint_roi >= 25: scores["roi"] = 90
    elif midpoint_roi >= 20: scores["roi"] = 75
    elif midpoint_roi >= 15: scores["roi"] = 60
    elif midpoint_roi >= 10: scores["roi"] = 35
    elif midpoint_roi >= 5: scores["roi"] = 15
    else: scores["roi"] = 0

    # Break-even berekening
    total_inv = prima.get("total_investment", 0)
    broker_sell = prima.get("broker_sell", 0)
    break_even = total_inv + broker_sell
    surface = listing.get("surface_m2", 1)
    break_even_m2 = break_even / surface if surface else 0
    reno_low = neighborhood.get("renovated_price_low", 0)

    threshold_text = (
        "ruim boven" if midpoint_roi >= 20 else
        "boven" if midpoint_roi >= 15 else
        "net onder" if midpoint_roi >= 10 else
        "ver onder"
    )
    be_text = (
        "comfortabel haalbaar" if break_even_m2 < reno_low else
        "haalbaar maar krap"
    )

    explanations["roi"] = (
        f"De midpoint ROI bedraagt {midpoint_roi:.1f}% "
        f"(prima casa {prima_roi:.1f}%, seconda casa {seconda_roi:.1f}%). "
        f"Dit ligt {threshold_text} de minimumdrempel van 15%. "
        f"Break-even verkoopprijs: EUR {break_even_m2:,.0f}/m2, wat {be_text} "
        f"is in {zone_name} (gerenoveerd gemiddelde EUR {reno_low:,}-{neighborhood.get('renovated_price_high', 0):,}/m2). "
        f"Netto winst prima casa: EUR {prima.get('net_profit', 0):,.0f}."
    )

    # ═══════════════════════════════════════════════════════
    # 2. MARGE SCORE (20%)
    # ═══════════════════════════════════════════════════════
    price_per_m2 = listing.get("price_per_m2", 0)
    sale_mid = sale_estimate.get("final_price_per_m2", {}).get("mid", neighborhood["renovated_price_mid"])

    spread = (sale_mid - price_per_m2) / price_per_m2 if price_per_m2 > 0 else 0

    if spread >= 0.70: scores["margin"] = 100
    elif spread >= 0.50: scores["margin"] = 80
    elif spread >= 0.35: scores["margin"] = 60
    elif spread >= 0.20: scores["margin"] = 40
    elif spread >= 0.10: scores["margin"] = 20
    else: scores["margin"] = 0

    reno_cost = params.get("renovation_cost_min_per_m2", 1200)
    margin_text = (
        "Ruime marge voor tegenvallers." if spread >= 0.50 else
        "Goede marge maar scherp inkopen is belangrijk." if spread >= 0.35 else
        "Krappe marge — onderhandeling op aankoopprijs is cruciaal." if spread >= 0.20 else
        "Onvoldoende marge voor een veilige flip."
    )

    explanations["margin"] = (
        f"Aankoopprijs EUR {price_per_m2:,.0f}/m2 vs. gerenoveerd gemiddelde EUR {sale_mid:,}/m2 "
        f"= bruto spread van {spread*100:.0f}%. "
        f"Na aftrek van renovatie (EUR {reno_cost}/m2) en bijkomende kosten "
        f"resteert een netto marge van EUR {prima.get('net_profit', 0):,.0f} (prima casa) "
        f"tot EUR {seconda.get('net_profit', 0):,.0f} (seconda casa). "
        f"{margin_text}"
    )

    # ═══════════════════════════════════════════════════════
    # 3. LOCATIE SCORE (15%)
    # ═══════════════════════════════════════════════════════
    if location_quality and location_quality.get("overall_score") is not None:
        scores["neighborhood"] = location_quality["overall_score"]
    else:
        scores["neighborhood"] = {3: 90, 2: 65, 1: 40}.get(neighborhood.get("priority", 1), 30)

    priority = neighborhood.get("priority", 1)
    yoy = neighborhood.get("yoy_growth", 0) * 100
    selling_t = neighborhood.get("avg_selling_time_months", 5)
    address = features.get("address") or listing.get("address", "")
    is_prem = is_premium_street(zone_name, address)

    # Bouw gedetailleerde locatie-uitleg met specifieke factoren
    loc_factors = location_quality.get("factors", []) if location_quality else []
    pos_factors = [f for f in loc_factors if f.get("category") == "positief"]
    neg_factors = [f for f in loc_factors if f.get("category") == "negatief"]

    pos_detail = ""
    if pos_factors:
        pos_items = "; ".join(f"{f['name']} (+{f['impact']})" for f in pos_factors)
        pos_detail = f"**Positief:** {pos_items}. "

    neg_detail = ""
    if neg_factors:
        neg_items = "; ".join(f"{f['name']} ({f['impact']})" for f in neg_factors)
        neg_detail = f"**Negatief:** {neg_items}. "

    explanations["neighborhood"] = (
        f"{zone_name} is een prioriteit-{priority} wijk. "
        f"Jaarlijkse prijsgroei: {yoy:.1f}%. Gemiddelde verkooptijd: {selling_t} maanden. "
        + (f"PREMIUM STRAAT gedetecteerd — bovengemiddelde vraag en prijs verwacht. " if is_prem else "")
        + pos_detail
        + neg_detail
        + (location_quality.get("summary", "") if location_quality else "")
    )

    # ═══════════════════════════════════════════════════════
    # 4. RISICO SCORE (15%)
    # ═══════════════════════════════════════════════════════
    risk_score = 100
    risk_flags: list[str] = []

    floor = listing.get("floor")
    if floor is not None and floor == 0 and not features.get("has_garden"):
        risk_score -= 25
        risk_flags.append("Begane grond zonder tuin (lagere verkoopwaarde, vochtrisico)")

    if floor is not None and floor >= 4 and listing.get("has_elevator") is False:
        risk_score -= 15
        risk_flags.append("Hoge verdieping zonder lift (beperkt koperspubliek)")

    energy_class = listing.get("energy_class", "")
    if energy_class and energy_class.upper() in ("F", "G"):
        risk_score -= 5
        risk_flags.append(f"Energieklasse {energy_class.upper()}: extra isolatiekosten")

    condo_fees = listing.get("condominium_fees")
    if condo_fees and condo_fees > 300:
        risk_score -= 10
        risk_flags.append(f"Hoge condominiumkosten (EUR {condo_fees:.0f}/maand)")

    if price_per_m2 > neighborhood.get("unrenovated_price_high", float("inf")):
        risk_score -= 20
        risk_flags.append(
            f"Aankoopprijs/m2 (EUR {price_per_m2:,.0f}) boven wijkgemiddelde "
            f"(EUR {neighborhood.get('unrenovated_price_high', 0):,.0f})"
        )

    if listing.get("surface_m2", 0) < 80:
        risk_score -= 20
        risk_flags.append("Oppervlakte <80m2: beperkt koperspubliek in luxesegment")

    # Feature-gebaseerde risico's
    if features.get("is_vincolo"):
        risk_score -= 30
        risk_flags.append("VINCOLO/BESCHERMD — renovatiebeperkingen en vertraging verwacht")
    if features.get("has_abuso"):
        risk_score -= 25
        risk_flags.append("Mogelijke illegale verbouwing (abuso edilizio)")
    if features.get("has_asbestos"):
        risk_score -= 40
        risk_flags.append("ASBEST gedetecteerd — hoge saneringskosten verwacht")
    if features.get("has_moisture"):
        risk_score -= 15
        risk_flags.append("Vochtprobleem gesignaleerd in beschrijving")
    if features.get("has_structural_issues"):
        risk_score -= 25
        risk_flags.append("Structurele problemen (scheuren, verzakking) gesignaleerd")
    if features.get("internal_dark"):
        risk_score -= 10
        risk_flags.append("Interne woning met weinig daglicht")

    # Condition-based
    condition = (listing.get("condition") or "").lower()
    if condition in ("ottimo / ristrutturato", "ristrutturato", "ottimo", "nuovo"):
        risk_score -= 15
        risk_flags.append(f"Al in bewoonbare staat: Dit beperkt de marge voor waardecreatie via renovatie")

    # Extra red flags uit beschrijving
    description_lower = (listing.get("title", "") + " " + listing.get("description", "")).lower()
    for keyword, penalty in RED_FLAGS.items():
        if keyword in description_lower and keyword not in ("vincolo",):
            risk_score += penalty  # penalties are negative
            risk_flags.append(f"Red flag '{keyword}' in beschrijving")

    scores["risk"] = max(0, risk_score)

    risk_label = (
        "Zeer laag risicoprofiel." if scores["risk"] >= 90 else
        "Aanvaardbaar risico met aandachtspunten." if scores["risk"] >= 70 else
        "VERHOOGD RISICO — extra due diligence nodig." if scores["risk"] >= 50 else
        "HOOG RISICO — overweeg dit pand over te slaan."
    )
    explanations["risk"] = (
        f"{risk_label} "
        f"{len(risk_flags)} risicofactor(en) gedetecteerd. "
        + ("Fysieke inspectie en due diligence door een geometra blijven essentieel." if risk_flags else
           "Geen bijzondere risico's gevonden — standaard due diligence volstaat.")
    )

    # ═══════════════════════════════════════════════════════
    # 5. LIQUIDITEIT SCORE (10%)
    # ═══════════════════════════════════════════════════════
    selling_months = neighborhood.get("avg_selling_time_months", 5)
    if selling_months <= 2: scores["liquidity"] = 100
    elif selling_months <= 3: scores["liquidity"] = 80
    elif selling_months <= 4: scores["liquidity"] = 60
    elif selling_months <= 6: scores["liquidity"] = 40
    else: scores["liquidity"] = 20

    explanations["liquidity"] = (
        f"Gemiddelde verkooptijd in {zone_name}: {selling_months} maanden. "
        f"Rome is momenteel een verkopersmarkt in topwijken. "
        f"Competitief biedgedrag neemt toe voor gerenoveerde woningen met goede energieprestatie. "
        f"Korter is beter: minder holding costs en minder marktrisico."
    )

    # ═══════════════════════════════════════════════════════
    # 6. OPPERVLAKTE SCORE (5%)
    # ═══════════════════════════════════════════════════════
    m2 = listing.get("surface_m2", 0)
    if 100 <= m2 <= 150: scores["surface"] = 100
    elif 80 <= m2 < 100 or 150 < m2 <= 180: scores["surface"] = 70
    elif 180 < m2 <= 200: scores["surface"] = 50
    else: scores["surface"] = 30

    size_text = (
        "Sweet spot voor luxe-flip (100-150m2)." if 100 <= m2 <= 150 else
        "Acceptabel maar net buiten de sweet spot." if 80 <= m2 <= 200 else
        "Te klein/groot voor optimale flip-marge."
    )
    explanations["surface"] = (
        f"Oppervlakte: {m2:.0f}m2. {size_text} "
        f"De ideale flip heeft 100-150m2: groot genoeg voor gezinnen, "
        f"maar niet zo duur dat het koperspubliek krimpt."
    )

    # ═══════════════════════════════════════════════════════
    # GEWOGEN TOTAALSCORE
    # ═══════════════════════════════════════════════════════
    weights = {
        "roi": 0.35,
        "margin": 0.20,
        "neighborhood": 0.15,
        "risk": 0.15,
        "liquidity": 0.10,
        "surface": 0.05,
    }

    total = sum(scores[k] * weights[k] for k in weights)

    return {
        "flip_score": round(total),
        "component_scores": scores,
        "score_explanations": explanations,
        "risk_flags": risk_flags,
        "weights": weights,
        "location_quality": location_quality,
    }
