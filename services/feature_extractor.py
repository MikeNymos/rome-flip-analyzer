"""
NLP Feature Extractie uit Italiaanse vastgoedbeschrijvingen.
Combineert gestructureerde velden + keyword-analyse van de beschrijving.
"""
from __future__ import annotations

import re


def extract_property_features(listing: dict) -> dict:
    """
    Extraheer gestructureerde kenmerken uit een genormaliseerde listing.
    Combineert bestaande velden + NLP-analyse van de Italiaanse beschrijving.
    """
    description = (listing.get("description") or "").lower()
    title = (listing.get("title") or "").lower()
    full_text = f"{title} {description}"

    features: dict = {}

    # ── VERDIEPING ──────────────────────────────────────────
    features["floor"] = listing.get("floor")
    features["is_top_floor"] = any(kw in full_text for kw in [
        "ultimo piano", "attico", "mansarda",
    ])
    features["is_ground_floor"] = (
        features["floor"] == 0
        or any(kw in full_text for kw in ["piano terra", "pianterreno"])
    )

    # ── LIFT ────────────────────────────────────────────────
    features["has_elevator"] = listing.get("has_elevator")
    if features["has_elevator"] is None:
        if "senza ascensore" in full_text or "no ascensore" in full_text:
            features["has_elevator"] = False
        elif "ascensore" in full_text:
            features["has_elevator"] = True

    # ── BUITENRUIMTE ───────────────────────────────────────
    features["has_terrace"] = any(kw in full_text for kw in [
        "terrazzo", "terrazza", "terrazzino", "lastrico",
        "roof terrace", "terrazza a livello",
    ])
    features["terrace_size"] = (
        "large" if any(kw in full_text for kw in [
            "ampio terrazzo", "grande terrazza", "lastrico solare",
            "terrazza abitabile", "terrazza panoramica",
        ]) else "small" if features["has_terrace"] else None
    )
    features["has_balcony"] = any(kw in full_text for kw in [
        "balcone", "balconata", "loggia",
    ])
    features["has_garden"] = any(kw in full_text for kw in [
        "giardino privato", "giardino esclusivo", "giardino condominiale",
    ])

    # ── PLAFONDS ───────────────────────────────────────────
    features["high_ceilings"] = any(kw in full_text for kw in [
        "soffitti alti", "altezza interna", "3 metri", "3,5 metri",
        "doppia altezza", "altezze generose", "soffitto alto",
    ])
    features["has_frescoes"] = any(kw in full_text for kw in [
        "affreschi", "soffitti decorati", "cassettoni",
        "soffitto a cassettoni", "volta a botte",
    ])

    # ── AUTHENTIEKE ELEMENTEN ──────────────────────────────
    features["original_floors"] = any(kw in full_text for kw in [
        "pavimento originale", "cotto", "cotto romano",
        "terrazzo alla veneziana", "graniglia", "marmo originale",
    ])
    features["original_moldings"] = any(kw in full_text for kw in [
        "stucchi", "cornici", "modanature", "rosoni",
        "decorazioni originali",
    ])
    features["marble_fireplace"] = any(kw in full_text for kw in [
        "camino", "caminetto", "camino in marmo",
    ])
    features["historic_doors"] = any(kw in full_text for kw in [
        "porte originali", "portone", "boiserie",
    ])

    # Tel authentieke elementen
    auth_count = sum([
        features["original_floors"],
        features["original_moldings"],
        features["marble_fireplace"],
        features["has_frescoes"],
        features["historic_doors"],
    ])
    features["authentic_element_count"] = auth_count

    # ── LICHTINVAL / ORIËNTATIE ────────────────────────────
    features["double_exposure"] = any(kw in full_text for kw in [
        "doppia esposizione", "tripla esposizione", "angolare",
    ])
    features["triple_exposure"] = "tripla esposizione" in full_text
    features["panoramic_view"] = any(kw in full_text for kw in [
        "panoramico", "vista panoramica", "vista su", "affaccio su",
        "cupola", "san pietro", "castel sant'angelo",
    ])
    features["monument_view"] = any(kw in full_text for kw in [
        "san pietro", "castel sant'angelo", "colosseo",
        "fori imperiali", "campidoglio", "altare della patria",
        "cupola", "vista su roma",
    ])
    features["luminous"] = any(kw in full_text for kw in [
        "luminoso", "luminosissimo", "molto luminoso",
        "pieno di luce", "ben illuminato",
    ])
    features["internal_dark"] = any(kw in full_text for kw in [
        "interno", "su cortile", "chiostrina", "poco luminoso",
    ])

    # ── GEBOUWKWALITEIT ────────────────────────────────────
    features["has_portineria"] = any(kw in full_text for kw in [
        "portineria", "portiere", "custode",
    ])
    features["palazzo_signorile"] = any(kw in full_text for kw in [
        "palazzo signorile", "stabile signorile", "palazzo d'epoca",
        "palazzo storico", "elegante stabile",
    ])

    # ── VINCOLO / RISICO'S ─────────────────────────────────
    features["is_vincolo"] = any(kw in full_text for kw in [
        "vincolo", "soprintendenza", "beni culturali", "tutela",
    ])
    features["has_abuso"] = any(kw in full_text for kw in [
        "abuso", "difformità", "non conforme", "sanabile",
    ])
    features["has_moisture"] = any(kw in full_text for kw in [
        "umidità", "umido", "infiltrazioni",
    ])
    features["has_asbestos"] = any(kw in full_text for kw in [
        "amianto", "eternit",
    ])
    features["has_structural_issues"] = any(kw in full_text for kw in [
        "crepe", "lesioni", "cedimento", "pericolante",
    ])

    # ── INDELING ───────────────────────────────────────────
    features["open_plan_possible"] = any(kw in full_text for kw in [
        "open space", "living", "soggiorno ampio",
        "cucina abitabile", "zona giorno",
    ])
    features["rational_layout"] = any(kw in full_text for kw in [
        "ben distribuito", "funzionale", "razionale",
        "ottima distribuzione",
    ])

    # ── EXTRA VOORZIENINGEN ────────────────────────────────
    features["has_parking"] = any(kw in full_text for kw in [
        "posto auto", "box auto", "garage", "parcheggio",
    ])
    features["has_storage"] = any(kw in full_text for kw in [
        "cantina", "soffitta", "ripostiglio",
    ])

    # ── STRAAT / ADRES ─────────────────────────────────────
    features["address"] = listing.get("address", "")

    # ── OPPERVLAKTE-EXTRACT (m²) ───────────────────────────
    m2_match = re.search(r"(\d{2,4})\s*m[q²]", full_text)
    if m2_match and not listing.get("surface_m2"):
        features["extracted_surface"] = int(m2_match.group(1))

    return features


# ── Premium straten per wijk ───────────────────────────────

PREMIUM_STREETS: dict[str, list[str]] = {
    "Prati": [
        "Via Cola di Rienzo", "Via dei Gracchi", "Via Ottaviano",
        "Via Crescenzio", "Viale Giulio Cesare", "Via Tacito",
        "Via Candia", "Piazza Cavour", "Via Ovidio",
        "Piazza Mazzini", "Via Andrea Doria", "Via Lepanto",
    ],
    "Trieste": [
        "Via Nomentana", "Piazza Buenos Aires", "Via Tagliamento",
        "Corso Trieste", "Via Salaria", "Viale Regina Margherita",
        "Via Nemorense", "Via Chiana", "Via Po",
    ],
    "Parioli": [
        "Viale Parioli", "Via dei Monti Parioli", "Piazza Ungheria",
        "Via Archimede", "Via Bertoloni", "Via Gramsci",
        "Via Chelini", "Piazza delle Muse",
    ],
    "Flaminio": [
        "Piazza del Popolo", "Via Flaminia", "Viale del Vignola",
        "Lungotevere Flaminio", "Via Guido Reni",
    ],
    "Centro Storico": [
        "Via del Corso", "Via dei Condotti", "Piazza Navona",
        "Via Giulia", "Via dei Coronari", "Campo de' Fiori",
    ],
    "Trastevere": [
        "Via della Lungara", "Piazza Santa Maria",
        "Viale Trastevere", "Via della Scala",
    ],
}


def is_premium_street(zone: str, address: str) -> bool:
    """Check of het adres op een premium straat ligt."""
    if not address:
        return False
    address_lower = address.lower()
    streets = PREMIUM_STREETS.get(zone, [])
    return any(s.lower() in address_lower for s in streets)
