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


# ══════════════════════════════════════════════════════════════
# STRAAT-KWALITEITSSYSTEEM — Tiered per wijk
# ══════════════════════════════════════════════════════════════
#
# Vier niveaus:
#   A (Premium)      : +6-8% — Beste adressen, hoogste vraag en prijzen
#   B (Goed)         : +3%   — Bovengemiddelde straten, goede reputatie
#   C (Gemiddeld)    : 0%    — Standaard (default, niet in een lijst)
#   D (Minder gewild): -3-5% — Luidruchtig, commercieel, perifeer
#
# Straten die niet in A/B/D voorkomen worden automatisch C.

STREET_QUALITY: dict[str, dict[str, list[str]]] = {
    "Prati": {
        "A": [
            "Piazza Mazzini", "Piazza Cavour", "Via Ovidio",
            "Via Marcantonio Colonna", "Via dei Gracchi",
            "Piazza dei Quiriti", "Via Pompeo Magno",
        ],
        "B": [
            "Via Cola di Rienzo", "Via Crescenzio", "Via Ottaviano",
            "Via Tacito", "Via Andrea Doria", "Viale Giulio Cesare",
            "Via Lepanto", "Via Fabio Massimo", "Via Paolo Emilio",
            "Via Germanico", "Via Virgilio",
        ],
        "D": [
            "Via Candia", "Via Barletta", "Via Leone IV",
            "Via degli Scipioni", "Via Tunisi", "Via Mocenigo",
            "Borgo", "Via della Conciliazione", "Via Pfeiffer",
        ],
    },
    "Mazzini - Delle Vittorie": {
        "A": [
            "Piazza Mazzini", "Viale Mazzini", "Via della Giuliana",
            "Via Trionfale",
        ],
        "B": [
            "Via Baldo degli Ubaldi", "Via degli Ammiragli",
            "Via Monte Zebio", "Via Monte Santo",
        ],
        "D": [
            "Via Cipro", "Via Angelo Emo", "Via Anastasio II",
        ],
    },
    "Trieste": {
        "A": [
            "Piazza Buenos Aires", "Via Tagliamento", "Via Chiana",
            "Via Po", "Corso Trieste", "Via Dora",
            "Via Isonzo", "Via Ticino",
        ],
        "B": [
            "Via Nomentana", "Via Nemorense", "Viale Regina Margherita",
            "Via Salaria", "Via Nizza", "Via Alessandria",
            "Via Asmara", "Via Bergamo",
        ],
        "D": [
            "Via Tiburtina", "Via di Priscilla", "Via Conca d'Oro",
            "Via Val d'Aosta", "Via Somalia",
        ],
    },
    "Parioli": {
        "A": [
            "Viale Parioli", "Via dei Monti Parioli", "Piazza delle Muse",
            "Via Archimede", "Via Stoppani", "Via Mercalli",
            "Via Antonelli", "Via Bruxelles",
        ],
        "B": [
            "Piazza Ungheria", "Via Bertoloni", "Via Chelini",
            "Via Gramsci", "Via Panama", "Via Lima",
            "Viale Bruno Buozzi", "Via Pinciana",
        ],
        "D": [
            "Viale Maresciallo Pilsudski", "Via Flaminia Vecchia",
            "Via dei Campi Sportivi", "Lungotevere delle Navi",
        ],
    },
    "Flaminio": {
        "A": [
            "Piazza del Popolo", "Lungotevere Flaminio",
            "Via Guido Reni", "Via Flaminia Vecchia",
        ],
        "B": [
            "Via Flaminia", "Viale del Vignola", "Via Donatello",
            "Via Pinturicchio", "Via Fracassini",
        ],
        "D": [
            "Viale Tiziano", "Viale della XVII Olimpiade",
            "Via delle Terme di Diocleziano",
        ],
    },
    "Centro Storico": {
        "A": [
            "Via Giulia", "Via dei Coronari", "Piazza Navona",
            "Via del Governo Vecchio", "Via dei Condotti",
            "Piazza di Spagna", "Via del Babuino",
            "Via Margutta", "Via di Monserrato",
            "Piazza Farnese", "Via dei Banchi Vecchi",
        ],
        "B": [
            "Via del Corso", "Campo de' Fiori", "Via dei Giubbonari",
            "Via dei Pettinari", "Piazza del Pantheon",
            "Via della Scrofa", "Via della Pace",
            "Rione Monti", "Via dei Serpenti",
        ],
        "D": [
            "Via Cavour", "Via Nazionale", "Via Marsala",
            "Via Gioberti", "Piazza dei Cinquecento",
            "Via Merulana", "Via dello Statuto",
            "Via Principe Amedeo",
        ],
    },
    "Trastevere": {
        "A": [
            "Piazza Santa Maria", "Via della Lungara",
            "Via dei Genovesi", "Via della Paglia",
            "Piazza San Cosimato",
        ],
        "B": [
            "Via della Scala", "Viale Trastevere",
            "Via Garibaldi", "Via della Renella",
            "Vicolo del Cedro",
        ],
        "D": [
            "Viale di Trastevere", "Via Portuense",
            "Via Ettore Rolli", "Via Induno",
        ],
    },
    "Testaccio": {
        "A": [
            "Piazza Testaccio", "Lungotevere Testaccio",
            "Via Marmorata",
        ],
        "B": [
            "Via Galvani", "Via Giovanni Branca",
            "Via Zabaglia",
        ],
        "D": [
            "Via Ostiense", "Via del Commercio",
            "Via Nicola Zabaglia",
        ],
    },
    "San Giovanni": {
        "A": [
            "Via Gallia", "Via Taranto",
            "Piazza Re di Roma",
        ],
        "B": [
            "Via Appia Nuova", "Viale Manzoni",
            "Via Monza", "Via La Spezia",
        ],
        "D": [
            "Via Tuscolana", "Via Casilina",
            "Via dello Scalo San Lorenzo",
        ],
    },
    "Monteverde": {
        "A": [
            "Via Carini", "Piazza San Giovanni di Dio",
            "Viale dei Quattro Venti",
        ],
        "B": [
            "Via Donna Olimpia", "Via Federico Ozanam",
            "Via di Monteverde",
        ],
        "D": [
            "Viale Trastevere", "Via Portuense",
            "Via Fonteiana",
        ],
    },
}

# Tier configuratie: adjustment percentages en labels
STREET_TIERS = {
    "A": {
        "label": "Premium straat",
        "label_short": "A-straat (premium)",
        "adjustment_pct": 0.06,
        "color": "#10B981",
    },
    "B": {
        "label": "Goede straat",
        "label_short": "B-straat (goed)",
        "adjustment_pct": 0.03,
        "color": "#34D399",
    },
    "C": {
        "label": "Gemiddelde straat",
        "label_short": "C-straat (gemiddeld)",
        "adjustment_pct": 0.0,
        "color": "#F59E0B",
    },
    "D": {
        "label": "Minder gewilde straat",
        "label_short": "D-straat (minder gewild)",
        "adjustment_pct": -0.04,
        "color": "#F97316",
    },
}


def get_street_quality(zone: str, address: str) -> dict:
    """
    Bepaalt de straatkwaliteit op basis van wijk en adres.

    Returns:
        Dict met tier (A/B/C/D), label, adjustment_pct, matched_street,
        explanation, en color.
    """
    if not address:
        return _build_street_result("C", zone, "", "Geen adres beschikbaar voor straatanalyse.")

    address_lower = address.lower()

    # Zoek in alle zone-varianten (fuzzy zone matching)
    zone_data = _match_zone_streets(zone)

    if zone_data:
        # Check A-straten
        for street in zone_data.get("A", []):
            if street.lower() in address_lower:
                return _build_street_result(
                    "A", zone, street,
                    f"{street} is een van de meest gewilde adressen in {zone}. "
                    f"Toplocatie met hoge vraag, sterke doorverkoop en structureel hogere prijzen/m²."
                )

        # Check B-straten
        for street in zone_data.get("B", []):
            if street.lower() in address_lower:
                return _build_street_result(
                    "B", zone, street,
                    f"{street} is een goede straat in {zone}. "
                    f"Bovengemiddelde vraag en residentieel karakter. "
                    f"Goede verkoopbaarheid na renovatie."
                )

        # Check D-straten
        for street in zone_data.get("D", []):
            if street.lower() in address_lower:
                return _build_street_result(
                    "D", zone, street,
                    f"{street} is een minder gewilde straat in {zone}. "
                    f"Factoren als verkeersdruk, commerciële activiteit of perifere ligging "
                    f"drukken de verkoopprijs t.o.v. het wijkgemiddelde."
                )

    # Geen match → C (gemiddeld)
    return _build_street_result(
        "C", zone, "",
        f"Geen specifieke straat-data beschikbaar voor dit adres in {zone}. "
        f"Standaard wijkgemiddelde wordt gehanteerd."
    )


def _match_zone_streets(zone: str) -> dict | None:
    """Zoekt de juiste zone in STREET_QUALITY met fuzzy matching."""
    if not zone:
        return None

    zone_lower = zone.lower()

    # Exacte match
    for key in STREET_QUALITY:
        if key.lower() == zone_lower:
            return STREET_QUALITY[key]

    # Deel-match (bv. "Prati" in "Prati - Mazzini - Delle Vittorie")
    for key in STREET_QUALITY:
        if key.lower() in zone_lower or zone_lower in key.lower():
            return STREET_QUALITY[key]

    # Keyword match voor samengestelde wijknamen
    zone_parts = set(zone_lower.replace("-", " ").replace("/", " ").split())
    for key in STREET_QUALITY:
        key_parts = set(key.lower().replace("-", " ").replace("/", " ").split())
        if zone_parts & key_parts:  # intersection
            return STREET_QUALITY[key]

    return None


def _build_street_result(tier: str, zone: str, matched_street: str, explanation: str) -> dict:
    """Bouwt het resultaat-dict voor een straatkwaliteitsbeoordeling."""
    tier_info = STREET_TIERS[tier]
    return {
        "tier": tier,
        "label": tier_info["label"],
        "label_short": tier_info["label_short"],
        "adjustment_pct": tier_info["adjustment_pct"],
        "matched_street": matched_street,
        "explanation": explanation,
        "color": tier_info["color"],
        "zone": zone,
    }


def is_premium_street(zone: str, address: str) -> bool:
    """Check of het adres op een premium straat ligt (backward compatible)."""
    result = get_street_quality(zone, address)
    return result["tier"] in ("A", "B")
