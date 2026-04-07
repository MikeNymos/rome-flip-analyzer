"""
Constanten voor de Belgische vastgoedanalyse module.
Keywords, rode vlaggen, staatmappings, EPC-labels.
"""
from __future__ import annotations

# Immoweb condition → intern renovatieniveau
CONDITION_MAP_BE = {
    "AS_NEW": "geen_renovatie",
    "GOOD": "opfrisbeurt",
    "TO_BE_DONE_UP": "lichte_renovatie",
    "TO_RENOVATE": "zware_renovatie",
    "TO_RESTORE": "buiten_scope",
}

CONDITION_LABELS_BE = {
    "AS_NEW": "Als nieuw",
    "GOOD": "Goed",
    "TO_BE_DONE_UP": "Te moderniseren",
    "TO_RENOVATE": "Te renoveren",
    "TO_RESTORE": "Af te breken / Casco",
}

# Renovatieniveaus met standaardkosten per m²
RENOVATION_LEVELS = {
    "geen_renovatie": {
        "label": "Geen renovatie",
        "cost_low": 0, "cost_mid": 0, "cost_high": 0,
        "duration_months": 0,
        "total_project_months": 3,
    },
    "opfrisbeurt": {
        "label": "Opfrisbeurt",
        "cost_low": 500, "cost_mid": 700, "cost_high": 900,
        "duration_months": 3.5,
        "total_project_months": 6,
        "description": "Schilderwerken, nieuwe vloeren, keukendeurtjes, verlichting, stopcontacten",
    },
    "lichte_renovatie": {
        "label": "Lichte renovatie",
        "cost_low": 900, "cost_mid": 1200, "cost_high": 1500,
        "duration_months": 5,
        "total_project_months": 7,
        "description": "Nieuwe keuken, badkamer(s), vloeren, schilderwerken, basis elektriciteit, binnendeuren",
    },
    "zware_renovatie": {
        "label": "Zware renovatie",
        "cost_low": 1500, "cost_mid": 1850, "cost_high": 2200,
        "duration_months": 7.5,
        "total_project_months": 10,
        "description": "Volledige strippen, elektriciteit, sanitair, verwarming, vloerisolatie, keuken, badkamers",
    },
    "buiten_scope": {
        "label": "Buiten scope (vergunningsplichtig)",
        "cost_low": 0, "cost_mid": 0, "cost_high": 0,
        "duration_months": 0,
        "total_project_months": 0,
    },
}

# Positieve keywords (Nederlands/Vlaams) in Immoweb beschrijvingen
POSITIVE_KEYWORDS_BE = {
    "lichtrijk": "Lichtrijke woning",
    "lumineus": "Lumineus",
    "terras": "Terras aanwezig",
    "dakterras": "Dakterras",
    "tuin": "Tuin aanwezig",
    "garage": "Garage",
    "autostaanplaats": "Parkeerplaats",
    "lift": "Lift aanwezig",
    "kelder": "Kelder",
    "berging": "Berging",
    "instapklaar": "Instapklaar",
    "gerenoveerd": "Gerenoveerd",
    "nieuwbouw": "Nieuwbouw",
    "energiezuinig": "Energiezuinig",
    "zonnepanelen": "Zonnepanelen",
    "warmtepomp": "Warmtepomp",
    "open keuken": "Open keuken",
    "parket": "Parketvloer",
    "sierlijsten": "Authentieke sierlijsten",
    "hoge plafonds": "Hoge plafonds",
    "authentiek": "Authentieke elementen",
    "art nouveau": "Art-nouveaustijl",
    "herenhuis": "Herenhuis",
    "stadstuin": "Stadstuin",
    "rustig gelegen": "Rustig gelegen",
    "nabij park": "Nabij park",
    "nabij openbaar vervoer": "Nabij OV",
}

# Negatieve keywords
NEGATIVE_KEYWORDS_BE = {
    "vochtig": "Vochtproblemen",
    "vochtschade": "Vochtschade",
    "asbest": "Asbest aanwezig",
    "enkele beglazing": "Enkele beglazing",
    "geen lift": "Geen lift",
    "drukke weg": "Drukke verkeersweg",
    "geluidsoverlast": "Geluidsoverlast",
    "geen parking": "Geen parkeerplaats",
    "geen kelder": "Geen kelder/berging",
    "verouderd": "Verouderde afwerking",
    "vervallen": "Vervallen staat",
    "leegstand": "Leegstand in omgeving",
    "industriezone": "Nabij industriegebied",
}

# Rode vlaggen — pand wordt gemarkeerd maar wel geanalyseerd
RED_FLAGS_BE = {
    "dragende muur": {"penalty": -20, "label": "Mogelijk vergunningsplichtig (dragende muur)"},
    "dakstructuur": {"penalty": -20, "label": "Mogelijk vergunningsplichtig (dakstructuur)"},
    "gevelwerken": {"penalty": -15, "label": "Mogelijk vergunningsplichtig (gevelwerken)"},
    "fundering": {"penalty": -25, "label": "Mogelijk vergunningsplichtig (fundering)"},
    "casco": {"penalty": -25, "label": "Casco — vergunningsplichtig"},
    "beschermd": {"penalty": -30, "label": "Beschermd monument / erfgoed"},
    "monument": {"penalty": -30, "label": "Beschermd monument"},
    "erfgoed": {"penalty": -25, "label": "Erfgoedrestricties"},
    "patrimoine": {"penalty": -25, "label": "Patrimoine (erfgoed)"},
    "asbest": {"penalty": -20, "label": "Asbest — saneringskosten"},
    "overstroming": {"penalty": -15, "label": "Overstromingsrisico"},
    "bodemsanering": {"penalty": -20, "label": "Bodemsaneringsverplichting"},
}

# EPC labels
EPC_LABELS = ["A", "B", "C", "D", "E", "F", "G"]

# Registratierechten per gewest (beroepsverkoper)
REGISTRATION_TAX_RATES = {
    "VLAANDEREN": 0.06,  # 6% sinds 01/01/2025
    "BRUSSEL": 0.08,     # 8%
    "WALLONIE": 0.05,    # 5%
}

# Notariskosten — degressieve schaal (2025-2026)
NOTARY_DEGRESSIVE_SCALE = [
    (7500, 0.0456),
    (17500, 0.0285),
    (30000, 0.0228),
    (45495, 0.0171),
    (64095, 0.0114),
    (250000, 0.0057),
    (float("inf"), 0.00057),
]


def calculate_notary_cost_degressive(purchase_price: float) -> float:
    """Berekent notariskosten via degressieve schaal."""
    cost = 0.0
    prev_limit = 0.0
    for limit, rate in NOTARY_DEGRESSIVE_SCALE:
        taxable = min(purchase_price, limit) - prev_limit
        if taxable <= 0:
            break
        cost += taxable * rate
        prev_limit = limit
    return round(cost + 500)  # +€500 administratiekosten


def calculate_notary_cost_simple(purchase_price: float) -> float:
    """Vereenvoudigde notariskosten (vuistregel)."""
    return round(3000 + purchase_price * 0.005)
