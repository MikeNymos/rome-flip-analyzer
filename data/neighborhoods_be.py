"""
Wijkbenchmarks voor Antwerpen & Zuidrand vastgoedmarkten.
Prijzen in €/m², gebaseerd op Immoweb-data, Statbel Q3 2025,
Notariële Barometer 2025 en marktkennis.

Alle prijzen betreffen gerenoveerde panden in goede staat (EPC C of beter).
"""
from __future__ import annotations

import difflib

# =============================================================================
# WIJKCLASSIFICATIE ANTWERPEN STAD
# =============================================================================

ANTWERP_NEIGHBORHOODS: dict[str, dict] = {
    # ─── TIER 1 — Premium ───────────────────────────────────
    "Het Zuid": {
        "postal_codes": ["2000", "2018"],
        "tier": 1,
        "score": 95,
        "apt_price_low": 3400, "apt_price_high": 4200, "apt_price_mid": 3800,
        "house_price_low": 3000, "house_price_high": 3800, "house_price_mid": 3400,
        "notes": "Cultureel hart, musea, horeca, jonge professionals + gezinnen",
    },
    "Zurenborg": {
        "postal_codes": ["2018"],
        "tier": 1,
        "score": 95,
        "apt_price_low": 3300, "apt_price_high": 4000, "apt_price_mid": 3650,
        "house_price_low": 3200, "house_price_high": 4000, "house_price_mid": 3600,
        "notes": "Iconische art-nouveau, zeer gewild, beperkt aanbod",
    },
    "Groen Kwartier": {
        "postal_codes": ["2018"],
        "tier": 1,
        "score": 93,
        "apt_price_low": 3500, "apt_price_high": 4300, "apt_price_mid": 3900,
        "house_price_low": 3200, "house_price_high": 3800, "house_price_mid": 3500,
        "notes": "Nieuwbouw-enclave, moderne afwerking, park",
    },
    "Stadspark-buurt": {
        "postal_codes": ["2018"],
        "tier": 1,
        "score": 92,
        "apt_price_low": 3200, "apt_price_high": 4000, "apt_price_mid": 3600,
        "house_price_low": 2900, "house_price_high": 3600, "house_price_mid": 3250,
        "notes": "Parkzijde premium, rustig residentieel",
    },
    "Eilandje": {
        "postal_codes": ["2000"],
        "tier": 1,
        "score": 85,
        "apt_price_low": 3100, "apt_price_high": 3900, "apt_price_mid": 3500,
        "house_price_low": 2800, "house_price_high": 3400, "house_price_mid": 3100,
        "notes": "Waterfront, MAS, Cadixwijk, sterk ontwikkelend",
    },

    # ─── TIER 2 — Goed ──────────────────────────────────────
    "Historisch Centrum": {
        "postal_codes": ["2000"],
        "tier": 2,
        "score": 75,
        "apt_price_low": 2800, "apt_price_high": 3500, "apt_price_mid": 3150,
        "house_price_low": 2500, "house_price_high": 3200, "house_price_mid": 2850,
        "notes": "Toerisme, commercieel, minder residentieel karakter",
    },
    "Berchem-Centrum": {
        "postal_codes": ["2600"],
        "tier": 2,
        "score": 78,
        "apt_price_low": 2700, "apt_price_high": 3300, "apt_price_mid": 3000,
        "house_price_low": 2500, "house_price_high": 3100, "house_price_mid": 2800,
        "notes": "Goed residentieel, goede verbinding, gezinnen",
    },
    "Berchem-Zuid": {
        "postal_codes": ["2600"],
        "tier": 2,
        "score": 80,
        "apt_price_low": 2800, "apt_price_high": 3400, "apt_price_mid": 3100,
        "house_price_low": 2600, "house_price_high": 3200, "house_price_mid": 2900,
        "notes": "Rustig, villawijk-karakter, Fruithoflaan",
    },
    "Wilrijk-Centrum": {
        "postal_codes": ["2610"],
        "tier": 2,
        "score": 76,
        "apt_price_low": 2600, "apt_price_high": 3200, "apt_price_mid": 2900,
        "house_price_low": 2400, "house_price_high": 3000, "house_price_mid": 2700,
        "notes": "Dorpsgevoel, goede voorzieningen, Bist",
    },
    "Deurne-Noord": {
        "postal_codes": ["2100"],
        "tier": 2,
        "score": 70,
        "apt_price_low": 2500, "apt_price_high": 3100, "apt_price_mid": 2800,
        "house_price_low": 2300, "house_price_high": 2900, "house_price_mid": 2600,
        "notes": "Nabij Rivierenhof, residentieel, gezinnen",
    },
    "Ekeren": {
        "postal_codes": ["2180"],
        "tier": 2,
        "score": 65,
        "apt_price_low": 2400, "apt_price_high": 2900, "apt_price_mid": 2650,
        "house_price_low": 2200, "house_price_high": 2800, "house_price_mid": 2500,
        "notes": "Groen, rustig, gezinnen, meer huizen dan appartementen",
    },

    # ─── TIER 2–3 — Gemengd ─────────────────────────────────
    "Theaterbuurt": {
        "postal_codes": ["2000"],
        "tier": 2,
        "score": 65,
        "apt_price_low": 2600, "apt_price_high": 3200, "apt_price_mid": 2900,
        "house_price_low": 2300, "house_price_high": 2900, "house_price_mid": 2600,
        "notes": "Commercieel, boven winkels, wisselende kwaliteit",
    },
    "Wilrijk-Zuid": {
        "postal_codes": ["2610"],
        "tier": 2,
        "score": 65,
        "apt_price_low": 2400, "apt_price_high": 2900, "apt_price_mid": 2650,
        "house_price_low": 2200, "house_price_high": 2700, "house_price_mid": 2450,
        "notes": "Verder van centrum, rustiger, Neerland",
    },

    # ─── TIER 3 — Betaalbaar / Opkomend ─────────────────────
    "Borgerhout Intra-Muros": {
        "postal_codes": ["2060"],
        "tier": 3,
        "score": 58,
        "apt_price_low": 2200, "apt_price_high": 2800, "apt_price_mid": 2500,
        "house_price_low": 2000, "house_price_high": 2500, "house_price_mid": 2250,
        "notes": "Gentrificatie, jonge kopers, goede marge, Turnhoutsebaan-noord",
    },
    "Borgerhout Extra-Muros": {
        "postal_codes": ["2140"],
        "tier": 3,
        "score": 55,
        "apt_price_low": 2300, "apt_price_high": 2800, "apt_price_mid": 2550,
        "house_price_low": 2100, "house_price_high": 2600, "house_price_mid": 2350,
        "notes": "Grotere panden, Te Boelaarlei, minder dynamisch",
    },
    "Deurne-Zuid": {
        "postal_codes": ["2100"],
        "tier": 3,
        "score": 58,
        "apt_price_low": 2300, "apt_price_high": 2800, "apt_price_mid": 2550,
        "house_price_low": 2100, "house_price_high": 2600, "house_price_mid": 2350,
        "notes": "Commercieel, Cruyslei, wisselend",
    },
    "Merksem-Centrum": {
        "postal_codes": ["2170"],
        "tier": 3,
        "score": 55,
        "apt_price_low": 2200, "apt_price_high": 2700, "apt_price_mid": 2450,
        "house_price_low": 2000, "house_price_high": 2500, "house_price_mid": 2250,
        "notes": "Betaalbaar, opkomend, goede tramverbinding",
    },
    "Hoboken-Centrum": {
        "postal_codes": ["2660"],
        "tier": 3,
        "score": 55,
        "apt_price_low": 2200, "apt_price_high": 2700, "apt_price_mid": 2450,
        "house_price_low": 2000, "house_price_high": 2500, "house_price_mid": 2250,
        "notes": "Dorpsgevoel, betaalbaar, goede tram",
    },

    # ─── TIER 3–4 — Risicovol ───────────────────────────────
    "Merksem-Noord": {
        "postal_codes": ["2170"],
        "tier": 3,
        "score": 45,
        "apt_price_low": 2000, "apt_price_high": 2500, "apt_price_mid": 2250,
        "house_price_low": 1900, "house_price_high": 2300, "house_price_mid": 2100,
        "notes": "Verder van centrum, minder dynamisch",
    },
    "Linkeroever": {
        "postal_codes": ["2050"],
        "tier": 3,
        "score": 42,
        "apt_price_low": 2000, "apt_price_high": 2500, "apt_price_mid": 2250,
        "house_price_low": 1800, "house_price_high": 2300, "house_price_mid": 2050,
        "notes": "Wisselend, nieuwbouwprojecten, langere verkooptijd",
    },
    "Kiel": {
        "postal_codes": ["2020"],
        "tier": 3,
        "score": 38,
        "apt_price_low": 1900, "apt_price_high": 2400, "apt_price_mid": 2150,
        "house_price_low": 1700, "house_price_high": 2200, "house_price_mid": 1950,
        "notes": "Sociale woningen, wisselend, enkele pockets van potentieel",
    },

    # ─── TIER 4 — Vermijden ─────────────────────────────────
    "Luchtbal": {
        "postal_codes": ["2030"],
        "tier": 4,
        "score": 25,
        "apt_price_low": 1800, "apt_price_high": 2200, "apt_price_mid": 2000,
        "house_price_low": 1600, "house_price_high": 2000, "house_price_mid": 1800,
        "notes": "Sociale woonblokken, havenomgeving, laag flip-potentieel",
    },
}

# =============================================================================
# WIJKCLASSIFICATIE ZUIDRAND
# =============================================================================

ZUIDRAND_NEIGHBORHOODS: dict[str, dict] = {
    "Mortsel-Centrum": {
        "postal_codes": ["2640"],
        "tier": 2, "score": 75,
        "apt_price_low": 2600, "apt_price_high": 3100, "apt_price_mid": 2850,
        "house_price_low": 2400, "house_price_high": 2900, "house_price_mid": 2650,
        "notes": "Goede treinverbinding, compact centrum, gezinnen",
    },
    "Mortsel-Rand": {
        "postal_codes": ["2640"],
        "tier": 2, "score": 68,
        "apt_price_low": 2400, "apt_price_high": 2900, "apt_price_mid": 2650,
        "house_price_low": 2200, "house_price_high": 2700, "house_price_mid": 2450,
        "notes": "Rustiger, meer huizen",
    },
    "Edegem": {
        "postal_codes": ["2650"],
        "tier": 2, "score": 78,
        "apt_price_low": 2600, "apt_price_high": 3200, "apt_price_mid": 2900,
        "house_price_low": 2500, "house_price_high": 3000, "house_price_mid": 2750,
        "notes": "Residentieel, goede scholen, populair bij gezinnen",
    },
    "Hove": {
        "postal_codes": ["2540"],
        "tier": 1, "score": 85,
        "apt_price_low": 2900, "apt_price_high": 3500, "apt_price_mid": 3200,
        "house_price_low": 2800, "house_price_high": 3400, "house_price_mid": 3100,
        "notes": "Villawijk, groen, exclusief, beperkt aanbod",
    },
    "Lint": {
        "postal_codes": ["2547"],
        "tier": 2, "score": 72,
        "apt_price_low": 2400, "apt_price_high": 2900, "apt_price_mid": 2650,
        "house_price_low": 2300, "house_price_high": 2800, "house_price_mid": 2550,
        "notes": "Dorps, rustig, betaalbaar, goede ligging",
    },
    "Kontich": {
        "postal_codes": ["2550"],
        "tier": 2, "score": 74,
        "apt_price_low": 2500, "apt_price_high": 3000, "apt_price_mid": 2750,
        "house_price_low": 2300, "house_price_high": 2800, "house_price_mid": 2550,
        "notes": "Goede bereikbaarheid (E19), mix woningen/appartementen",
    },
    "Boechout": {
        "postal_codes": ["2530"],
        "tier": 2, "score": 74,
        "apt_price_low": 2500, "apt_price_high": 3000, "apt_price_mid": 2750,
        "house_price_low": 2400, "house_price_high": 2900, "house_price_mid": 2650,
        "notes": "Groen, dorps, goede scholen, gezinnen",
    },
    "Aartselaar": {
        "postal_codes": ["2630"],
        "tier": 2, "score": 65,
        "apt_price_low": 2400, "apt_price_high": 2900, "apt_price_mid": 2650,
        "house_price_low": 2200, "house_price_high": 2700, "house_price_mid": 2450,
        "notes": "Commercieel + residentieel, bereikbaar",
    },
    "Hemiksem": {
        "postal_codes": ["2620"],
        "tier": 3, "score": 55,
        "apt_price_low": 2100, "apt_price_high": 2600, "apt_price_mid": 2350,
        "house_price_low": 2000, "house_price_high": 2400, "house_price_mid": 2200,
        "notes": "Betaalbaar, minder dynamisch, verbeterpotentieel",
    },
    "Schelle": {
        "postal_codes": ["2627"],
        "tier": 2, "score": 65,
        "apt_price_low": 2300, "apt_price_high": 2800, "apt_price_mid": 2550,
        "house_price_low": 2200, "house_price_high": 2700, "house_price_mid": 2450,
        "notes": "Dorps, rustig, beperkt aanbod",
    },
    "Ranst": {
        "postal_codes": ["2520"],
        "tier": 2, "score": 65,
        "apt_price_low": 2300, "apt_price_high": 2800, "apt_price_mid": 2550,
        "house_price_low": 2200, "house_price_high": 2700, "house_price_mid": 2450,
        "notes": "Landelijk, huizenmarkt, minder appartementen",
    },
    "Mechelen": {
        "postal_codes": ["2800"],
        "tier": 2, "score": 75,
        "apt_price_low": 2600, "apt_price_high": 3200, "apt_price_mid": 2900,
        "house_price_low": 2400, "house_price_high": 2900, "house_price_mid": 2650,
        "notes": "Stijgend, goed OV, attractieve binnenstad",
    },
}

# Combineer alle wijken
ALL_NEIGHBORHOODS_BE: dict[str, dict] = {
    **ANTWERP_NEIGHBORHOODS,
    **ZUIDRAND_NEIGHBORHOODS,
}

# Focuspostcodes
FOCUS_POSTCODES = [
    "2000", "2018", "2020", "2030", "2040", "2050", "2060",
    "2100", "2140", "2170", "2180",
    "2520", "2530", "2540", "2547", "2550",
    "2600", "2610", "2620", "2627", "2630", "2640", "2650", "2660",
    "2800",
]

# Staatscorrectie: niet-gerenoveerde prijs t.o.v. gerenoveerde prijs
CONDITION_PRICE_FACTOR = {
    "AS_NEW": 1.00,
    "GOOD": 0.85,
    "TO_BE_DONE_UP": 0.70,
    "TO_RENOVATE": 0.55,
}

# Typecorrectie op referentieprijs
PROPERTY_TYPE_FACTOR = {
    "APARTMENT": 1.00,
    "STUDIO": 0.95,
    "PENTHOUSE": 1.10,
    "DUPLEX": 1.00,
    "TRIPLEX": 1.00,
    "GROUND_FLOOR": 0.95,
    "LOFT": 1.02,
    "HOUSE_ROW": 0.90,       # Rijwoning (1-2 gevels)
    "HOUSE_SEMI": 0.95,      # Halfopen (2-3 gevels)
    "HOUSE_DETACHED": 1.00,  # Open bebouwing (4 gevels)
    "OTHER": 0.95,
}


def match_neighborhood(postal_code: str, municipality: str = "") -> dict | None:
    """
    Matcht een postcode + gemeente naar een bekende wijk.
    Retourneert het wijkobject of None als niet gevonden.
    """
    postal_code = str(postal_code).strip()

    # Exacte postcode match
    for name, data in ALL_NEIGHBORHOODS_BE.items():
        if postal_code in data["postal_codes"]:
            # Als er meerdere wijken zijn met dezelfde postcode, probeer gemeente-match
            return {"name": name, **data}

    # Fuzzy match op gemeente
    if municipality:
        muni_lower = municipality.strip().lower()
        for name, data in ALL_NEIGHBORHOODS_BE.items():
            if muni_lower in name.lower() or name.lower() in muni_lower:
                return {"name": name, **data}

    return None


def get_reference_price(postal_code: str, property_type: str = "APARTMENT",
                         municipality: str = "") -> dict:
    """
    Haalt de referentieprijs per m² op voor een postcode en pandtype.
    """
    neighborhood = match_neighborhood(postal_code, municipality)

    if not neighborhood:
        # Default voor onbekende postcode
        return {
            "neighborhood": "Onbekend",
            "tier": 3,
            "score": 50,
            "ref_price_low": 2200,
            "ref_price_mid": 2600,
            "ref_price_high": 3000,
        }

    is_house = property_type in ("HOUSE_ROW", "HOUSE_SEMI", "HOUSE_DETACHED", "HOUSE")
    if is_house:
        return {
            "neighborhood": neighborhood["name"],
            "tier": neighborhood["tier"],
            "score": neighborhood["score"],
            "ref_price_low": neighborhood["house_price_low"],
            "ref_price_mid": neighborhood["house_price_mid"],
            "ref_price_high": neighborhood["house_price_high"],
        }

    return {
        "neighborhood": neighborhood["name"],
        "tier": neighborhood["tier"],
        "score": neighborhood["score"],
        "ref_price_low": neighborhood["apt_price_low"],
        "ref_price_mid": neighborhood["apt_price_mid"],
        "ref_price_high": neighborhood["apt_price_high"],
    }
