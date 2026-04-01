"""
Wijkbenchmarks voor Rome vastgoedmarkten.
Prijzen in €/m², gebaseerd op marktanalyse 2024-2025.
"""
from __future__ import annotations


import difflib

NEIGHBORHOOD_BENCHMARKS: dict[str, dict] = {
    "Prati": {
        "unrenovated_price_low": 4200,
        "unrenovated_price_high": 5500,
        "renovated_price_low": 7000,
        "renovated_price_mid": 8000,
        "renovated_price_high": 9500,
        "yoy_growth": 0.059,
        "avg_selling_time_months": 3,
        "risk_level": "low",
        "priority": 3,
        "notes": "Topkeuze. Vaticaan-nabij, elegante architectuur, Metro C boost verwacht.",
    },
    "Trieste": {
        "unrenovated_price_low": 3800,
        "unrenovated_price_high": 4800,
        "renovated_price_low": 5800,
        "renovated_price_mid": 6500,
        "renovated_price_high": 7500,
        "yoy_growth": 0.06,
        "avg_selling_time_months": 4,
        "risk_level": "low",
        "priority": 3,
        "notes": "Beste prijs-kwaliteitverhouding. Lagere instap, sterke marge.",
    },
    "Parioli": {
        "unrenovated_price_low": 5000,
        "unrenovated_price_high": 6000,
        "renovated_price_low": 6800,
        "renovated_price_mid": 7500,
        "renovated_price_high": 9000,
        "yoy_growth": 0.08,
        "avg_selling_time_months": 3,
        "risk_level": "medium",
        "priority": 2,
        "notes": "Gevestigde luxewijk. Hogere instap, stabiele vraag. Risico: hoge aankoopprijs.",
    },
    "Flaminio": {
        "unrenovated_price_low": 4500,
        "unrenovated_price_high": 5500,
        "renovated_price_low": 6200,
        "renovated_price_mid": 7000,
        "renovated_price_high": 8500,
        "yoy_growth": 0.05,
        "avg_selling_time_months": 4,
        "risk_level": "medium",
        "priority": 2,
        "notes": "Opkomend, grenzend aan Parioli. MAXXI museum. Diversificatie-optie.",
    },
    "Centro Storico": {
        "unrenovated_price_low": 6000,
        "unrenovated_price_high": 10000,
        "renovated_price_low": 9000,
        "renovated_price_mid": 12000,
        "renovated_price_high": 15000,
        "yoy_growth": 0.09,
        "avg_selling_time_months": 4,
        "risk_level": "high",
        "priority": 1,
        "notes": "Topsegment maar hoog vincolo-risico. Alleen voor ervaren flippers.",
    },
}

DEFAULT_BENCHMARK = {
    "unrenovated_price_low": 2800,
    "unrenovated_price_high": 4000,
    "renovated_price_low": 4500,
    "renovated_price_mid": 5500,
    "renovated_price_high": 7000,
    "yoy_growth": 0.05,
    "avg_selling_time_months": 5,
    "risk_level": "medium",
    "priority": 1,
    "notes": "Overige wijk — gebruik met voorzichtigheid.",
}

# Alias-mapping voor fuzzy matching van wijknamen uit Immobiliare.it
ZONE_ALIASES: dict[str, str] = {
    "prati": "Prati",
    "mazzini": "Prati",
    "prati/mazzini": "Prati",
    "prati - mazzini": "Prati",
    "prati-mazzini": "Prati",
    "quartiere prati": "Prati",
    "rione prati": "Prati",
    "cola di rienzo": "Prati",
    "delle vittorie": "Prati",
    "trieste": "Trieste",
    "salario": "Trieste",
    "trieste/salario": "Trieste",
    "trieste - salario": "Trieste",
    "trieste-salario": "Trieste",
    "quartiere trieste": "Trieste",
    "nomentano": "Trieste",
    "parioli": "Parioli",
    "quartiere parioli": "Parioli",
    "parioli - pinciano": "Parioli",
    "pinciano": "Parioli",
    "flaminio": "Flaminio",
    "quartiere flaminio": "Flaminio",
    "flaminio - ponte milvio": "Flaminio",
    "ponte milvio": "Flaminio",
    "centro storico": "Centro Storico",
    "centro": "Centro Storico",
    "rione monti": "Centro Storico",
    "trastevere": "Centro Storico",
    "navona": "Centro Storico",
    "pantheon": "Centro Storico",
    "campo de' fiori": "Centro Storico",
    "campo marzio": "Centro Storico",
    "trevi": "Centro Storico",
    "spagna": "Centro Storico",
}


def match_zone(zone_name: str) -> str:
    """
    Mapt een wijknaam uit Immobiliare.it naar een bekende benchmark-wijk.
    Gebruikt eerst exacte alias-matching, daarna fuzzy matching.
    """
    if not zone_name:
        return "_default"

    zone_lower = zone_name.strip().lower()

    # 1. Exacte alias match
    if zone_lower in ZONE_ALIASES:
        return ZONE_ALIASES[zone_lower]

    # 2. Gedeeltelijke match: check of een alias voorkomt in de zone-naam
    for alias, canonical in ZONE_ALIASES.items():
        if alias in zone_lower or zone_lower in alias:
            return canonical

    # 3. Fuzzy match tegen bekende benchmark-wijknamen
    known_names = list(NEIGHBORHOOD_BENCHMARKS.keys())
    matches = difflib.get_close_matches(zone_name, known_names, n=1, cutoff=0.5)
    if matches:
        return matches[0]

    # 4. Fuzzy match tegen aliases
    all_aliases = list(ZONE_ALIASES.keys())
    matches = difflib.get_close_matches(zone_lower, all_aliases, n=1, cutoff=0.5)
    if matches:
        return ZONE_ALIASES[matches[0]]

    return "_default"


def get_neighborhood_benchmarks(zone_name: str) -> dict:
    """
    Haalt benchmarkdata op voor een wijk, met fuzzy matching.
    """
    matched = match_zone(zone_name)
    if matched == "_default" or matched not in NEIGHBORHOOD_BENCHMARKS:
        result = DEFAULT_BENCHMARK.copy()
        result["matched_zone"] = "Overig"
        result["original_zone"] = zone_name
        return result

    result = NEIGHBORHOOD_BENCHMARKS[matched].copy()
    result["matched_zone"] = matched
    result["original_zone"] = zone_name
    return result


def get_all_zones() -> list[str]:
    """Retourneert alle bekende wijknamen."""
    return list(NEIGHBORHOOD_BENCHMARKS.keys())
