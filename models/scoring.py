"""
Flip Score berekening (0-100) op basis van gewogen componenten.
Inclusief Nederlandse toelichtingen per component.
"""
from __future__ import annotations

from data.neighborhoods import get_neighborhood_benchmarks
from data.constants import RED_FLAGS


def calculate_flip_score(listing: dict, analysis: dict, params: dict) -> dict:
    """
    Berekent een gewogen Flip Score van 0-100 met toelichtingen.

    Componenten en gewichten:
    - ROI Score (35%):        Hoe hoger de verwachte ROI, hoe beter
    - Marge Score (20%):      Spread tussen aankoop/m2 en gerenoveerd/m2
    - Locatie Score (15%):    Multi-factor locatieanalyse
    - Risico Score (15%):     Afwezigheid van risicofactoren
    - Liquiditeit Score (10%): Verkoopbaarheid na renovatie
    - Oppervlakte Score (5%):  Sweet spot 100-150m2
    """
    scores = {}
    explanations = {}
    neighborhood = analysis.get("neighborhood_data", get_neighborhood_benchmarks(listing.get("zone", "")))
    location_quality = analysis.get("location_quality", {})
    sale_estimate = analysis.get("sale_price_estimate", {})

    # 1. ROI SCORE (35%)
    midpoint_roi = analysis["midpoint_roi"]
    prima_roi = analysis.get("prima_casa", analysis.get("optimistic", {})).get("roi", 0)

    if midpoint_roi >= 30:
        scores["roi"] = 100
    elif midpoint_roi >= 25:
        scores["roi"] = 90
    elif midpoint_roi >= 20:
        scores["roi"] = 75
    elif midpoint_roi >= 15:
        scores["roi"] = 60
    elif midpoint_roi >= 10:
        scores["roi"] = 35
    elif midpoint_roi >= 5:
        scores["roi"] = 15
    else:
        scores["roi"] = 0

    roi_label = (
        "Uitstekend" if scores["roi"] >= 80 else
        "Goed" if scores["roi"] >= 60 else
        "Matig" if scores["roi"] >= 35 else
        "Onvoldoende"
    )
    explanations["roi"] = (
        f"Midpoint ROI: {midpoint_roi:.1f}% (prima casa: {prima_roi:.1f}%). "
        f"Score: {scores['roi']}/100 ({roi_label}). "
        f"Een ROI van 15%+ is het minimale doel voor een flip-investering."
    )

    # 2. MARGE SCORE (20%)
    price_per_m2 = listing.get("price_per_m2", 0)
    sale_mid = sale_estimate.get("final_price_per_m2", {}).get("mid", neighborhood["renovated_price_mid"])

    if price_per_m2 > 0:
        spread = (sale_mid - price_per_m2) / price_per_m2
    else:
        spread = 0

    if spread >= 0.70:
        scores["margin"] = 100
    elif spread >= 0.50:
        scores["margin"] = 80
    elif spread >= 0.35:
        scores["margin"] = 60
    elif spread >= 0.20:
        scores["margin"] = 40
    elif spread >= 0.10:
        scores["margin"] = 20
    else:
        scores["margin"] = 0

    explanations["margin"] = (
        f"Aankoopprijs: EUR {price_per_m2:,.0f}/m2. "
        f"Geschatte verkoopprijs na renovatie: EUR {sale_mid:,.0f}/m2. "
        f"Spread: {spread*100:.0f}%. "
        f"Hoe groter de spread, hoe meer ruimte voor winst na aftrek van alle kosten."
    )

    # 3. LOCATIE SCORE (15%) — nu multi-factor
    if location_quality and location_quality.get("overall_score") is not None:
        scores["neighborhood"] = location_quality["overall_score"]
        explanations["neighborhood"] = location_quality.get("summary", "Geen locatieanalyse beschikbaar.")
    else:
        scores["neighborhood"] = {3: 90, 2: 65, 1: 40}.get(neighborhood.get("priority", 1), 30)
        explanations["neighborhood"] = f"Locatiescore gebaseerd op wijkprioriteit: {neighborhood.get('priority', 1)}/3."

    # 4. RISICO SCORE (15%)
    risk_score = 100
    risk_flags = []

    # Begane grond
    floor = listing.get("floor")
    if floor is not None and floor == 0:
        risk_score -= 25
        risk_flags.append("Begane grond: lagere verkoopwaarde, minder licht, veiligheidsrisico")

    # Geen lift bij hoge verdieping
    if floor is not None and floor >= 4 and listing.get("has_elevator") is False:
        risk_score -= 15
        risk_flags.append("Hoge verdieping zonder lift: beperkt koperspubliek, langere verkooptijd")

    # Slechte energieklasse
    energy_class = listing.get("energy_class", "")
    if energy_class and energy_class.upper() in ["F", "G"]:
        risk_score -= 5
        risk_flags.append(f"Energieklasse {energy_class.upper()}: extra isolatiekosten bij renovatie")

    # Hoge condominiumkosten
    condo_fees = listing.get("condominium_fees")
    if condo_fees and condo_fees > 300:
        risk_score -= 10
        risk_flags.append(f"Hoge condominiumkosten (EUR {condo_fees:.0f}/maand): drukt de netto opbrengst")

    # Prijs per m2 boven wijkgemiddelde
    if price_per_m2 > neighborhood.get("unrenovated_price_high", float("inf")):
        risk_score -= 20
        risk_flags.append(
            f"Aankoopprijs/m2 (EUR {price_per_m2:,.0f}) boven wijkgemiddelde "
            f"(EUR {neighborhood.get('unrenovated_price_high', 0):,.0f}): beperkte marge"
        )

    # Kleine oppervlakte
    if listing.get("surface_m2", 0) < 80:
        risk_score -= 20
        risk_flags.append("Oppervlakte <80m2: beperkt koperspubliek in luxesegment")

    # Vincolo-indicatoren in beschrijving
    vincolo_keywords = ["vincolo", "soprintendenza", "beni culturali", "tutela", "monumento"]
    description_lower = (
        listing.get("title", "") + " " + listing.get("description", "")
    ).lower()

    if any(kw in description_lower for kw in vincolo_keywords):
        risk_score -= 30
        risk_flags.append("VINCOLO/BESCHERMD MONUMENT: vertraging en beperkingen bij renovatie verwacht")

    # Extra red flags uit beschrijving
    for keyword, penalty in RED_FLAGS.items():
        if keyword in description_lower and keyword not in ["vincolo"]:
            risk_score += penalty
            risk_flags.append(f"Red flag '{keyword}': risico op extra kosten of juridische problemen")

    scores["risk"] = max(0, risk_score)

    risk_label = (
        "Laag risico" if scores["risk"] >= 80 else
        "Gemiddeld risico" if scores["risk"] >= 50 else
        "Hoog risico"
    )
    explanations["risk"] = (
        f"Risicoscore: {scores['risk']}/100 ({risk_label}). "
        + (f"{len(risk_flags)} waarschuwing(en) gevonden." if risk_flags else "Geen risicovlaggen gevonden.")
    )

    # 5. LIQUIDITEIT SCORE (10%)
    selling_months = neighborhood.get("avg_selling_time_months", 5)
    if selling_months <= 2:
        scores["liquidity"] = 100
    elif selling_months <= 3:
        scores["liquidity"] = 80
    elif selling_months <= 4:
        scores["liquidity"] = 60
    elif selling_months <= 6:
        scores["liquidity"] = 40
    else:
        scores["liquidity"] = 20

    explanations["liquidity"] = (
        f"Gemiddelde verkooptijd in {neighborhood.get('matched_zone', 'deze wijk')}: "
        f"{selling_months} maanden. "
        f"Korter is beter: minder holding costs en minder marktrisico."
    )

    # 6. OPPERVLAKTE SCORE (5%)
    m2 = listing.get("surface_m2", 0)
    if 100 <= m2 <= 150:
        scores["surface"] = 100
    elif 80 <= m2 < 100 or 150 < m2 <= 180:
        scores["surface"] = 70
    elif 180 < m2 <= 200:
        scores["surface"] = 50
    else:
        scores["surface"] = 30

    explanations["surface"] = (
        f"Oppervlakte: {m2:.0f}m2. "
        f"De sweet spot voor flips is 100-150m2: groot genoeg voor gezinnen, "
        f"niet te duur voor de doelgroep. "
        + ("Ideale maat!" if 100 <= m2 <= 150 else
           "Acceptabel." if 80 <= m2 <= 200 else
           "Buiten de ideale range.")
    )

    # === GEWOGEN TOTAALSCORE ===
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
