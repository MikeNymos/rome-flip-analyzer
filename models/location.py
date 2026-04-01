"""
Multi-factor locatiekwaliteitsanalyse.
Beoordeelt locatie op basis van wijk, verdieping, lift, terras, oriëntatie, staat, etc.
"""
from __future__ import annotations

import re


def assess_location_quality(listing: dict, neighborhood_data: dict) -> dict:
    """
    Beoordeelt de locatiekwaliteit van een pand op basis van meerdere factoren.

    Returns:
        Dict met overall_score (0-100), factors[], summary, positive_count, negative_count.
    """
    factors = []
    score = 50  # neutrale startwaarde

    zone_name = neighborhood_data.get("matched_zone", listing.get("zone", "Onbekend"))

    # --- 1. WIJK PRIORITEIT & GROEI ---
    priority = neighborhood_data.get("priority", 1)
    yoy = neighborhood_data.get("yoy_growth", 0)
    selling_time = neighborhood_data.get("avg_selling_time_months", 5)

    if priority == 3:
        impact = 20
        factors.append({
            "name": f"Topwijk: {zone_name}",
            "impact": impact,
            "explanation": (
                f"{zone_name} is een prioriteit-3 wijk met hoge vraag onder kopers. "
                f"Jaarlijkse prijsgroei: {yoy*100:.1f}%. "
                f"Gemiddelde verkooptijd: {selling_time} maanden. "
                f"Sterk verhuurd- en doorverkooppotentieel."
            ),
            "category": "positief",
        })
        score += impact
    elif priority == 2:
        impact = 10
        factors.append({
            "name": f"Goede wijk: {zone_name}",
            "impact": impact,
            "explanation": (
                f"{zone_name} is een prioriteit-2 wijk met stabiele vraag. "
                f"Jaarlijkse prijsgroei: {yoy*100:.1f}%. "
                f"Gemiddelde verkooptijd: {selling_time} maanden."
            ),
            "category": "positief",
        })
        score += impact
    else:
        impact = -5
        factors.append({
            "name": f"Mindere wijk: {zone_name}",
            "impact": impact,
            "explanation": (
                f"{zone_name} heeft een lagere prioriteit voor flip-investeringen. "
                f"Lagere vraag en langere verkooptijden ({selling_time} maanden). "
                f"Hogere korting op vraagprijs mogelijk nodig."
            ),
            "category": "negatief",
        })
        score += impact

    # Groeipremie
    if yoy >= 0.07:
        factors.append({
            "name": "Sterke prijsgroei",
            "impact": 5,
            "explanation": (
                f"Met {yoy*100:.1f}% jaarlijkse prijsgroei presteert {zone_name} bovengemiddeld. "
                f"Dit verhoogt de kans dat de verkoopprijs bij oplevering hoger uitvalt dan geschat."
            ),
            "category": "positief",
        })
        score += 5

    # --- 2. VERDIEPING + LIFT ---
    floor = listing.get("floor")
    has_elevator = listing.get("has_elevator")

    if floor is not None:
        if floor == 0:
            impact = -15
            factors.append({
                "name": "Begane grond",
                "impact": impact,
                "explanation": (
                    "Begane grond woningen in Rome hebben een lagere verkoopwaarde: "
                    "minder licht, meer straatlawaai, veiligheidsrisico, "
                    "en minder privacy. Verwacht 5-10% lagere verkoopprijs/m2."
                ),
                "category": "negatief",
            })
            score += impact
        elif floor >= 4 and has_elevator:
            impact = 10
            factors.append({
                "name": f"Hoge verdieping ({floor}e) met lift",
                "impact": impact,
                "explanation": (
                    f"Verdieping {floor} met lift is zeer gewild: meer licht, uitzicht, "
                    f"minder lawaai. Kopers betalen een premium van 3-8% t.o.v. lagere verdiepingen."
                ),
                "category": "positief",
            })
            score += impact
        elif floor >= 4 and has_elevator is False:
            impact = -15
            factors.append({
                "name": f"Hoge verdieping ({floor}e) zonder lift",
                "impact": impact,
                "explanation": (
                    f"Verdieping {floor} zonder lift beperkt het koperspubliek aanzienlijk. "
                    f"Vooral ouderen en gezinnen met kleine kinderen haken af. "
                    f"Verwacht 5-10% lagere verkoopprijs en langere verkooptijd."
                ),
                "category": "negatief",
            })
            score += impact
        elif 1 <= floor <= 3 and has_elevator:
            impact = 5
            factors.append({
                "name": f"Middenverdieping ({floor}e) met lift",
                "impact": impact,
                "explanation": (
                    "Middenverdieping met lift is goed verkoopbaar. "
                    "Bereikbaar voor alle doelgroepen, voldoende licht en privacy."
                ),
                "category": "positief",
            })
            score += impact
        elif 1 <= floor <= 3 and has_elevator is False:
            impact = -5
            factors.append({
                "name": f"Verdieping {floor} zonder lift",
                "impact": impact,
                "explanation": (
                    f"Verdieping {floor} zonder lift is acceptabel maar niet ideaal. "
                    f"Beperkt de doelgroep enigszins (ouderen, mobiliteit)."
                ),
                "category": "negatief",
            })
            score += impact

    # --- 3. TERRAS / BALKON ---
    has_terrace = _detect_feature(listing, ["terrazzo", "terrazza", "terrace", "terrass"])
    has_balcony = _detect_feature(listing, ["balcone", "balcony", "balkon"])

    if has_terrace:
        impact = 15
        factors.append({
            "name": "Terras aanwezig",
            "impact": impact,
            "explanation": (
                "Een terras is een van de meest waardeverhogende kenmerken in Rome. "
                "Kopers betalen een significant premium (5-10%) voor buitenruimte, "
                "vooral in combinatie met een hoge verdieping en uitzicht."
            ),
            "category": "positief",
        })
        score += impact
    elif has_balcony:
        impact = 5
        factors.append({
            "name": "Balkon aanwezig",
            "impact": impact,
            "explanation": (
                "Een balkon voegt waarde toe en verhoogt de aantrekkelijkheid. "
                "Minder impact dan een terras, maar nog steeds gewild bij kopers."
            ),
            "category": "positief",
        })
        score += impact

    # --- 4. ORIENTATIE / LICHT ---
    has_double_exposure = _detect_in_text(listing, [
        "doppia esposizione", "double exposure", "dubbele orientatie",
        "esposizione doppia",
    ])
    is_bright = _detect_in_text(listing, [
        "luminoso", "luminosa", "panoramico", "panoramica", "bright", "licht",
    ])

    if has_double_exposure:
        impact = 8
        factors.append({
            "name": "Dubbele orientatie",
            "impact": impact,
            "explanation": (
                "Dubbele oriëntatie (doppia esposizione) zorgt voor meer natuurlijk licht "
                "en betere ventilatie. Dit is een belangrijk verkoopargument in Rome "
                "en kan 3-5% extra opleveren."
            ),
            "category": "positief",
        })
        score += impact
    elif is_bright:
        impact = 3
        factors.append({
            "name": "Lumineus pand",
            "impact": impact,
            "explanation": (
                "Het pand wordt omschreven als licht/lumineus. "
                "Natuurlijk licht is een belangrijk koopcriterium in Rome."
            ),
            "category": "positief",
        })
        score += impact

    # --- 5. STAAT VAN HET PAND ---
    condition = (listing.get("condition") or "").lower()
    if any(kw in condition for kw in ["ristrutturare", "da ristrutturare", "renovate"]):
        factors.append({
            "name": "Te renoveren",
            "impact": 0,
            "explanation": (
                "Het pand is te renoveren — ideaal voor een flip-investering. "
                "Dit biedt de mogelijkheid om naar eigen inzicht te renoveren "
                "en maximale waardecreatie te realiseren."
            ),
            "category": "neutraal",
        })
    elif any(kw in condition for kw in ["buono", "abitabile", "good", "habitable"]):
        impact = -8
        factors.append({
            "name": "Al in bewoonbare staat",
            "impact": impact,
            "explanation": (
                "Het pand is al in goede/bewoonbare staat. "
                "Dit beperkt de marge voor waardecreatie via renovatie: "
                "de aankoopprijs/m2 zal dichter bij de gerenoveerde prijs liggen."
            ),
            "category": "negatief",
        })
        score += impact
    elif any(kw in condition for kw in ["nuovo", "new", "costruzione"]):
        impact = -15
        factors.append({
            "name": "Nieuwbouw/recent gerenoveerd",
            "impact": impact,
            "explanation": (
                "Het pand is nieuwbouw of recent gerenoveerd. "
                "Geen ruimte voor flip-waardecreatie via renovatie. "
                "De marge zit puur in marktgroei of onderhandeling."
            ),
            "category": "negatief",
        })
        score += impact

    # --- 6. GEBOUWKENMERKEN ---
    has_portiere = _detect_in_text(listing, ["portiere", "portineria", "doorman", "concierge"])
    if has_portiere:
        impact = 3
        factors.append({
            "name": "Portier/conciërge",
            "impact": impact,
            "explanation": (
                "Een gebouw met portier duidt op een hogere standing. "
                "Dit trekt kopers in het premiumsegment aan."
            ),
            "category": "positief",
        })
        score += impact

    has_high_ceilings = _detect_in_text(listing, [
        "soffitti alti", "high ceilings", "hoge plafonds", "altezza",
    ])
    if has_high_ceilings:
        impact = 5
        factors.append({
            "name": "Hoge plafonds",
            "impact": impact,
            "explanation": (
                "Hoge plafonds (typisch 3m+) zijn kenmerkend voor premiumwoningen in Rome. "
                "Ze vergroten het gevoel van ruimte en verhogen de verkoopwaarde met 3-5%."
            ),
            "category": "positief",
        })
        score += impact

    # --- Clamp score ---
    score = max(0, min(100, score))

    # --- Samenvatting ---
    pos_count = sum(1 for f in factors if f["category"] == "positief")
    neg_count = sum(1 for f in factors if f["category"] == "negatief")

    if score >= 75:
        summary = f"Uitstekende locatie met {pos_count} positieve factoren. Sterk flip-potentieel."
    elif score >= 60:
        summary = f"Goede locatie met {pos_count} positieve en {neg_count} negatieve factoren."
    elif score >= 40:
        summary = f"Gemiddelde locatie. Let op {neg_count} risicofactor(en)."
    else:
        summary = f"Zwakke locatie met {neg_count} negatieve factoren. Hoog risico voor flip."

    return {
        "overall_score": score,
        "factors": factors,
        "summary": summary,
        "positive_count": pos_count,
        "negative_count": neg_count,
    }


def _detect_feature(listing: dict, keywords: list[str]) -> bool:
    """Detecteert of een feature aanwezig is in feature_labels, features, of description."""
    # Check feature_labels
    for label in listing.get("feature_labels", []):
        label_lower = str(label).lower()
        if any(kw in label_lower for kw in keywords):
            return True

    # Check features
    for feat in listing.get("features", []):
        feat_lower = str(feat).lower()
        if any(kw in feat_lower for kw in keywords):
            return True

    # Check description
    return _detect_in_text(listing, keywords)


def _detect_in_text(listing: dict, keywords: list[str]) -> bool:
    """Detecteert keywords in titel + beschrijving + condition."""
    text = " ".join([
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("condition", ""),
    ]).lower()
    return any(kw in text for kw in keywords)
