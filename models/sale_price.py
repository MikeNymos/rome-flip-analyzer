"""
Verkoopprijsschatting met volledige onderbouwing.
Combineert wijkbenchmarks met pandspecifieke correcties.
"""
from __future__ import annotations

from utils.helpers import format_eur, format_eur_per_m2


def estimate_sale_price(listing: dict, neighborhood_data: dict, location_quality: dict) -> dict:
    """
    Schat de verkoopprijs na renovatie met volledige onderbouwing.

    Returns:
        Dict met base_price_per_m2, adjustments[], final_price_per_m2 (low/mid/high),
        total_price (low/mid/high), justification_text, neighborhood_name.
    """
    surface = listing["surface_m2"]
    zone_name = neighborhood_data.get("matched_zone", listing.get("zone", "Onbekend"))

    base_low = neighborhood_data["renovated_price_low"]
    base_mid = neighborhood_data["renovated_price_mid"]
    base_high = neighborhood_data["renovated_price_high"]

    adjustments = []

    # --- 1. VERDIEPING + LIFT ---
    floor = listing.get("floor")
    has_elevator = listing.get("has_elevator")

    if floor is not None:
        if floor >= 4 and has_elevator:
            adj = 0.05
            adjustments.append({
                "name": f"Hoge verdieping ({floor}e) met lift",
                "adjustment_pct": adj,
                "explanation": (
                    f"Verdieping {floor} met lift: kopers betalen een premium van ~5% "
                    f"voor meer licht, uitzicht en minder straatlawaai."
                ),
            })
        elif floor == 0:
            adj = -0.08
            adjustments.append({
                "name": "Begane grond",
                "adjustment_pct": adj,
                "explanation": (
                    "Begane grond woningen verkopen voor 5-10% minder: "
                    "minder licht, privacy en veiligheidsperceptie."
                ),
            })
        elif floor >= 4 and has_elevator is False:
            adj = -0.06
            adjustments.append({
                "name": f"Hoge verdieping ({floor}e) zonder lift",
                "adjustment_pct": adj,
                "explanation": (
                    "Hoge verdieping zonder lift vermindert het koperspubliek. "
                    "Verwacht 5-8% korting op de verkoopprijs."
                ),
            })

    # --- 2. TERRAS / BALKON ---
    has_terrace = _has_feature(listing, ["terrazzo", "terrazza", "terrace"])
    has_balcony = _has_feature(listing, ["balcone", "balcony"])

    if has_terrace:
        adjustments.append({
            "name": "Terras",
            "adjustment_pct": 0.07,
            "explanation": (
                "Een terras is zeer gewild in Rome en levert een premium op van 5-10%. "
                "Buitenruimte is schaars en sterk gewaardeerd."
            ),
        })
    elif has_balcony:
        adjustments.append({
            "name": "Balkon",
            "adjustment_pct": 0.03,
            "explanation": (
                "Een balkon voegt ~3% toe aan de verkoopwaarde. "
                "Minder impact dan een terras maar nog steeds gewild."
            ),
        })

    # --- 3. DUBBELE ORIENTATIE ---
    has_double_exp = _has_text(listing, [
        "doppia esposizione", "esposizione doppia", "double exposure",
    ])
    if has_double_exp:
        adjustments.append({
            "name": "Dubbele orientatie",
            "adjustment_pct": 0.03,
            "explanation": (
                "Dubbele oriëntatie zorgt voor meer licht en ventilatie. "
                "Kopers waarderen dit met een premium van ~3%."
            ),
        })

    # --- 4. HOGE PLAFONDS ---
    has_high_ceil = _has_text(listing, [
        "soffitti alti", "high ceilings", "altezza",
    ])
    if has_high_ceil:
        adjustments.append({
            "name": "Hoge plafonds",
            "adjustment_pct": 0.03,
            "explanation": (
                "Hoge plafonds (3m+) zijn typisch voor premiumwoningen in Rome. "
                "Ze vergroten het ruimtegevoel en verhogen de waarde met ~3%."
            ),
        })

    # --- 5. PORTIER ---
    has_portiere = _has_text(listing, ["portiere", "portineria", "concierge"])
    if has_portiere:
        adjustments.append({
            "name": "Portier/conciërge",
            "adjustment_pct": 0.02,
            "explanation": (
                "Een portier in het gebouw duidt op hogere standing "
                "en trekt kopers in het premiumsegment aan (+2%)."
            ),
        })

    # --- 6. OPPERVLAKTE SWEET SPOT ---
    if 100 <= surface <= 150:
        adjustments.append({
            "name": "Ideale oppervlakte (100-150m2)",
            "adjustment_pct": 0.02,
            "explanation": (
                "Woningen van 100-150m2 zijn het meest gevraagd in het "
                "gerenoveerde segment: groot genoeg voor gezinnen, "
                "maar niet te duur voor de doelgroep."
            ),
        })
    elif surface < 70:
        adjustments.append({
            "name": "Kleine oppervlakte (<70m2)",
            "adjustment_pct": -0.03,
            "explanation": (
                "Woningen onder 70m2 zijn minder gewild in het premiumsegment. "
                "Het koperspubliek is beperkter, wat de prijs/m2 drukt."
            ),
        })

    # --- Berekening ---
    total_adj_pct = sum(a["adjustment_pct"] for a in adjustments)

    # Voeg EUR/m2 impact toe aan elke adjustment
    for a in adjustments:
        a["adjustment_eur_per_m2"] = round(base_mid * a["adjustment_pct"])

    final_low = round(base_low * (1 + total_adj_pct))
    final_mid = round(base_mid * (1 + total_adj_pct))
    final_high = round(base_high * (1 + total_adj_pct))

    # --- Onderbouwingstekst ---
    justification_lines = [
        f"Geschatte verkoopprijs na renovatie voor {zone_name}:",
        f"",
        f"Basisprijs gerenoveerd in {zone_name}:",
        f"  Laag: {format_eur_per_m2(base_low)} | Midden: {format_eur_per_m2(base_mid)} | Hoog: {format_eur_per_m2(base_high)}",
        f"  (Bron: marktanalyse vergelijkbare transacties in {zone_name})",
    ]

    if adjustments:
        justification_lines.append("")
        justification_lines.append("Correcties op basis van pandkenmerken:")
        for a in adjustments:
            sign = "+" if a["adjustment_pct"] > 0 else ""
            justification_lines.append(
                f"  {sign}{a['adjustment_pct']*100:.0f}% ({sign}{a['adjustment_eur_per_m2']} EUR/m2) "
                f"- {a['name']}"
            )

    justification_lines.extend([
        "",
        f"Totale correctie: {'+' if total_adj_pct >= 0 else ''}{total_adj_pct*100:.0f}%",
        f"Geschatte prijs/m2: {format_eur_per_m2(final_low)} - {format_eur_per_m2(final_mid)} - {format_eur_per_m2(final_high)}",
        f"Geschatte totaalprijs ({surface:.0f}m2): {format_eur(final_low * surface)} - {format_eur(final_mid * surface)} - {format_eur(final_high * surface)}",
    ])

    return {
        "base_price_per_m2": {"low": base_low, "mid": base_mid, "high": base_high},
        "adjustments": adjustments,
        "total_adjustment_pct": total_adj_pct,
        "final_price_per_m2": {"low": final_low, "mid": final_mid, "high": final_high},
        "total_price": {
            "low": final_low * surface,
            "mid": final_mid * surface,
            "high": final_high * surface,
        },
        "justification_text": "\n".join(justification_lines),
        "neighborhood_name": zone_name,
        "neighborhood_notes": neighborhood_data.get("notes", ""),
    }


def _has_feature(listing: dict, keywords: list[str]) -> bool:
    """Check feature_labels en features arrays."""
    for label in listing.get("feature_labels", []):
        if any(kw in str(label).lower() for kw in keywords):
            return True
    for feat in listing.get("features", []):
        if any(kw in str(feat).lower() for kw in keywords):
            return True
    return _has_text(listing, keywords)


def _has_text(listing: dict, keywords: list[str]) -> bool:
    """Check titel + beschrijving."""
    text = " ".join([
        listing.get("title", ""),
        listing.get("description", ""),
    ]).lower()
    return any(kw in text for kw in keywords)
