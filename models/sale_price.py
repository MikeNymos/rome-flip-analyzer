"""
Verkoopprijsschatting met hedonisch prijsmodel (12+ correctiefactoren).
Combineert wijkbenchmarks met pandspecifieke correcties.
"""
from __future__ import annotations

from utils.helpers import format_eur, format_eur_per_m2
from services.feature_extractor import is_premium_street


def estimate_sale_price(
    listing: dict,
    neighborhood_data: dict,
    location_quality: dict,
    features: dict | None = None,
) -> dict:
    """
    Schat de verkoopprijs na renovatie via hedonisch model met 12+ correctiefactoren.

    Args:
        listing: Genormaliseerde listing dict.
        neighborhood_data: Wijkbenchmarks.
        location_quality: Locatiekwaliteitsanalyse.
        features: Output van extract_property_features(). Als None, basisanalyse.

    Returns:
        Dict met base_price_per_m2, adjustments[], final_price_per_m2 (low/mid/high),
        total_price (low/mid/high), justification_text, neighborhood_name.
    """
    surface = listing["surface_m2"]
    zone_name = neighborhood_data.get("matched_zone", listing.get("zone", "Onbekend"))
    feat = features if isinstance(features, dict) else {}

    base_low = neighborhood_data["renovated_price_low"]
    base_mid = neighborhood_data["renovated_price_mid"]
    base_high = neighborhood_data["renovated_price_high"]

    adjustments: list[dict] = []

    # ── 1. VERDIEPING + LIFT ───────────────────────────────
    floor = feat.get("floor") or listing.get("floor")
    has_elevator = feat.get("has_elevator") if feat.get("has_elevator") is not None else listing.get("has_elevator")
    is_top = feat.get("is_top_floor", False)
    is_ground = feat.get("is_ground_floor", False)
    has_terrace = feat.get("has_terrace", False)

    if is_top and has_terrace:
        _add(adjustments, "Attiek met dakterras", 0.12,
             "Ultimo piano met terras is het meest gewilde pandtype in Rome. "
             "Kopers betalen 10-15% premium voor uitzicht, licht en buitenruimte.")
    elif is_top:
        _add(adjustments, "Ultimo piano", 0.05,
             "Bovenste verdieping biedt meer licht, privacy en uitzicht. "
             "Premium van ~5% t.o.v. tussenverdiepingen.")
    elif floor is not None and floor >= 4 and has_elevator:
        _add(adjustments, f"Hoge verdieping ({floor}e) met lift", 0.05,
             f"Verdieping {floor} met lift is zeer gewild: meer licht, uitzicht, minder lawaai. "
             f"Kopers betalen een premium van ~5% voor meer licht, uitzicht en minder straatlawaai.")
    elif floor is not None and floor >= 4 and has_elevator is False:
        penalty = -0.05 if floor == 4 else -0.10 if floor == 5 else -0.15
        _add(adjustments, f"Hoge verdieping ({floor}e) zonder lift", penalty,
             f"Verdieping {floor} zonder lift beperkt het koperspubliek aanzienlijk. "
             f"Ouderen en gezinnen met jonge kinderen haken af.")
    elif is_ground and feat.get("has_garden"):
        _add(adjustments, "Begane grond met tuin", -0.03,
             "Begane grond met privétuin compenseert deels het nadeel van de lage verdieping. "
             "Tuin is zeldzaam in het centrum van Rome.")
    elif is_ground:
        _add(adjustments, "Begane grond zonder tuin", -0.10,
             "Begane grond woningen verkopen voor 8-12% minder: "
             "minder licht, privacy, veiligheidsperceptie en vochtrisico.")
    elif floor is not None and floor == 1:
        _add(adjustments, "Eerste verdieping", -0.03,
             "Eerste verdieping heeft minder licht dan hogere etages. "
             "Kleine korting van ~3% t.o.v. middenverdiepingen.")

    # ── 2. BUITENRUIMTE ───────────────────────────────────
    # (alleen als niet al in verdieping meegerekend)
    if has_terrace and not (is_top and has_terrace):
        size = feat.get("terrace_size", "small")
        if size == "large":
            _add(adjustments, "Groot terras", 0.10,
                 "Een groot terras (lastrico solare, terrazza abitabile) is extreem "
                 "waardevol in Rome. Premium van 8-12%.")
        else:
            _add(adjustments, "Terras", 0.06,
                 "Een terras is zeer gewild in Rome. Buitenruimte is schaars "
                 "en levert een premium op van 5-8%.")
    elif feat.get("has_balcony"):
        _add(adjustments, "Balkon", 0.02,
             "Een balkon voegt ~2% toe aan de verkoopwaarde. "
             "Minder impact dan een terras maar positief voor kopersperceptie.")
    if feat.get("has_garden") and not is_ground:
        _add(adjustments, "Privétuin", 0.05,
             "Privétuin is zeldzaam en waardevol in Rome. Premium van ~5%.")

    # ── 3. PLAFONDHOOGTE ──────────────────────────────────
    if feat.get("has_frescoes"):
        _add(adjustments, "Gedecoreerde plafonds / cassettoni", 0.05,
             "Fresco's, cassettoniplafonds of decoratieve stucwerken zijn uniek "
             "en niet reproduceerbaar. Sterk gewild in het luxesegment (+5%).")
    elif feat.get("high_ceilings"):
        _add(adjustments, "Hoge plafonds (3m+)", 0.04,
             "Hoge plafonds (>3m) bieden een ruimtelijk gevoel dat niet te repliceren is "
             "in nieuwbouw. Premium van ~4% in het gerenoveerde segment.")

    # ── 4. AUTHENTIEKE ELEMENTEN ──────────────────────────
    auth_count = feat.get("authentic_element_count", 0)
    if auth_count >= 3:
        _add(adjustments, "Meerdere authentieke elementen", 0.06,
             f"{auth_count} originele elementen (vloeren, stucwerk, haard, deuren). "
             "Niet-reproduceerbare authenticiteit trekt premium kopers aan (+6%).")
    elif auth_count == 2:
        _add(adjustments, "Authentieke elementen", 0.04,
             "Originele architecturale elementen (terrazzo alla veneziana, cotto, "
             "sierlijsten) voegen ~4% toe aan de verkoopwaarde.")
    elif auth_count == 1:
        _add(adjustments, "Authentiek element", 0.02,
             "Eén origineel element (vloer, stucwerk of haard) is een "
             "positief verkooppunt voor het premiumsegment (+2%).")

    # ── 5. LICHTINVAL / ORIËNTATIE ────────────────────────
    if feat.get("monument_view"):
        _add(adjustments, "Monumentaal uitzicht", 0.10,
             "Uitzicht op een herkenbaar monument (San Pietro, Castel Sant'Angelo) "
             "is het ultieme verkoopargument. Premium van 8-12%.")
    elif feat.get("panoramic_view"):
        _add(adjustments, "Panoramisch uitzicht", 0.08,
             "Panoramisch uitzicht verhoogt de waarde met ~8%. "
             "Bijzonder waardevol in combinatie met hoge verdieping.")
    elif feat.get("triple_exposure"):
        _add(adjustments, "Drievoudige oriëntatie", 0.06,
             "Tripla esposizione biedt optimale lichtinval en doorluchting "
             "gedurende de hele dag. Premium van ~6%.")
    elif feat.get("double_exposure"):
        _add(adjustments, "Dubbele oriëntatie", 0.04,
             "Doppia esposizione zorgt voor natuurlijke ventilatie en meer "
             "daglicht. Sterk gewaardeerd door kopers (+4%).")

    if feat.get("internal_dark") and not feat.get("panoramic_view"):
        _add(adjustments, "Intern / weinig licht", -0.08,
             "Interne woningen (op binnenplaats/chiostrina) met weinig "
             "natuurlijk licht verkopen voor 6-10% minder.")

    # ── 6. MICRO-LOCATIE / PREMIUM STRAAT ─────────────────
    address = feat.get("address") or listing.get("address", "")
    if is_premium_street(zone_name, address):
        _add(adjustments, "Premium straat", 0.05,
             f"Adres op een topstraat in {zone_name} levert structureel "
             f"hogere verkoopprijzen op. Premium van ~5%.")

    # ── 7. ENERGIEPRESTATIE ───────────────────────────────
    energy = listing.get("energy_class", "")
    if energy and energy.upper() in ("A", "A+", "A1", "A2", "A3", "A4", "B"):
        _add(adjustments, f"Goede energieklasse ({energy})", 0.03,
             "EU-richtlijnen maken energieklasse steeds belangrijker. "
             "Klasse A/B levert ~3% premium op bij verkoop.")

    # ── 8. OPPERVLAKTE ────────────────────────────────────
    if 100 <= surface <= 150:
        _add(adjustments, "Ideale oppervlakte (100-150m2)", 0.02,
             "Woningen van 100-150m2 zijn het meest gevraagd in het "
             "gerenoveerde segment: groot genoeg voor gezinnen, "
             "maar niet te duur voor de doelgroep.")
    elif 70 <= surface < 90:
        _add(adjustments, "Compacte oppervlakte (70-90m2)", 0.03,
             "Compacte woningen hebben een hogere prijs/m2 door hoge vraag "
             "van starters en investeerders.")
    elif surface < 70:
        _add(adjustments, "Kleine oppervlakte (<70m2)", -0.03,
             "Woningen onder 70m2 zijn minder gewild in het premiumsegment. "
             "Het koperspubliek is beperkter.")
    elif 150 < surface <= 200:
        _add(adjustments, "Grote oppervlakte (150-200m2)", -0.03,
             "Grotere woningen hebben een lagere prijs/m2. "
             "Het totale prijskaartje beperkt het koperspubliek.")
    elif surface > 200:
        _add(adjustments, "Zeer grote oppervlakte (>200m2)", -0.06,
             "Woningen >200m2 zijn niche. De prijs/m2 daalt aanzienlijk "
             "doordat slechts weinig kopers dit segment betreden.")

    # ── 9. GEBOUWKWALITEIT ────────────────────────────────
    if feat.get("palazzo_signorile"):
        _add(adjustments, "Palazzo signorile", 0.05,
             "Een palazzo d'epoca met verzorgde gevel en representatieve entree "
             "trekt premium kopers aan. Meerwaarde van ~5%.")
    elif feat.get("has_portineria"):
        _add(adjustments, "Portier/conciërge", 0.02,
             "Een portier in het gebouw duidt op hogere standing "
             "en trekt kopers in het premiumsegment aan (+2%).")

    condo = listing.get("condominium_fees") or 0
    if condo > 400:
        _add(adjustments, f"Hoge VvE-kosten (€{condo:.0f}/mnd)", -0.04,
             "Condominiumkosten >€400/mnd schrikken kopers af. "
             "Dit drukt de verkoopprijs met ~4%.")
    elif condo > 300:
        _add(adjustments, f"Verhoogde VvE-kosten (€{condo:.0f}/mnd)", -0.02,
             "Condominiumkosten >€300/mnd zijn bovengemiddeld en "
             "een lichte negatieve factor bij verkoop (-2%).")

    # ── 10. INDELING ──────────────────────────────────────
    if feat.get("rational_layout"):
        _add(adjustments, "Goede indeling", 0.02,
             "Rationele, functionele indeling met goede ruimteverdeling "
             "is een positief verkooppunt (+2%).")
    elif feat.get("open_plan_possible"):
        _add(adjustments, "Open plan mogelijk", 0.02,
             "Mogelijkheid tot open woonkeuken-concept is sterk "
             "gewild bij het moderne koperspubliek (+2%).")

    # ── 11. VINCOLO / RISICO ──────────────────────────────
    if feat.get("is_vincolo"):
        _add(adjustments, "Vincolo (beschermd monument)", -0.05,
             "Vincolo-status beperkt renovatiemogelijkheden. "
             "Langere doorlooptijd en hogere kosten drukken de marge (-5%).")

    # ── BEREKENING ────────────────────────────────────────
    total_adj_pct = sum(a["adjustment_pct"] for a in adjustments)

    # Voeg EUR/m2 impact toe aan elke adjustment
    for a in adjustments:
        a["adjustment_eur_per_m2"] = round(base_mid * a["adjustment_pct"])

    final_low = round(base_low * (1 + total_adj_pct))
    final_mid = round(base_mid * (1 + total_adj_pct))
    final_high = round(base_high * (1 + total_adj_pct))

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
        "neighborhood_name": zone_name,
        "neighborhood_notes": neighborhood_data.get("notes", ""),
        "data_period": neighborhood_data.get("data_period", ""),
        "sources": neighborhood_data.get("sources", []),
        "comparable_search_url": neighborhood_data.get("comparable_search_url", ""),
        "recent_transactions": neighborhood_data.get("recent_transactions", []),
    }


def _add(adjustments: list, name: str, pct: float, explanation: str):
    """Helper: voeg een correctie toe."""
    adjustments.append({
        "name": name,
        "adjustment_pct": pct,
        "explanation": explanation,
    })
