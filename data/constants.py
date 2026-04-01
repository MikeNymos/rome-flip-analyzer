"""
Constanten voor belastingtarieven, vaste kosten en keyword-lijsten.
"""
from __future__ import annotations


# NLP-analyse keywords voor Italiaanse beschrijvingen
POSITIVE_KEYWORDS = {
    "luminoso": "Lichtrijk",
    "panoramico": "Panoramisch uitzicht",
    "terrazzo": "Terras aanwezig",
    "balcone": "Balkon",
    "soffitti alti": "Hoge plafonds",
    "parquet": "Parketvloer (bestaand)",
    "doppia esposizione": "Dubbele oriëntatie",
    "silenzioso": "Rustig",
    "vista": "Uitzicht",
    "ultimo piano": "Bovenste verdieping",
    "attico": "Penthouse",
    "ristrutturato": "Gerenoveerd",
    "ascensore": "Lift aanwezig",
    "cantina": "Kelder/berging",
    "posto auto": "Parkeerplaats",
    "giardino": "Tuin",
    "portiere": "Portier aanwezig",
}

NEGATIVE_KEYWORDS = {
    "vincolo": "VINCOLO — beschermd monument",
    "soprintendenza": "Soprintendenza vereist",
    "abuso": "Mogelijk illegale verbouwing",
    "piano terra": "Begane grond",
    "seminterrato": "Souterrain",
    "da rifare": "Compleet te renoveren (structureel)",
    "umidità": "Vochtproblemen",
    "amianto": "Asbest",
    "rumoroso": "Lawaaierig",
    "senza ascensore": "Geen lift",
    "condominio alto": "Hoge VME-kosten",
    "nuda proprietà": "Bloot eigendom (bewoner aanwezig)",
    "occupato": "Bezet pand",
}

RED_FLAGS = {
    "vincolo": -30,
    "abuso": -25,
    "amianto": -40,
    "umidità": -15,
    "seminterrato": -20,
    "nuda proprietà": -35,
    "occupato": -30,
}

# Condities mapping
CONDITION_MAP = {
    "da_ristrutturare": "Te renoveren",
    "da ristrutturare": "Te renoveren",
    "buono": "Goede staat",
    "ottimo": "Uitstekende staat",
    "nuovo": "Nieuwbouw",
    "abitabile": "Bewoonbaar",
    "discreto": "Redelijke staat",
}
