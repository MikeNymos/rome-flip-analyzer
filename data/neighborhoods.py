"""
Wijkbenchmarks voor Rome vastgoedmarkten.
Prijzen in €/m², gebaseerd op marktanalyse 2024-2025.
Met directe bronverwijzingen naar OMI en Immobiliare.it.
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
        "data_period": "H2 2024 – Q1 2025",
        "sources": [
            {
                "name": "Immobiliare.it Prijstrends Prati",
                "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/prati/",
                "type": "market_trend",
            },
            {
                "name": "OMI — Agenzia delle Entrate (Zone E1-E2)",
                "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari",
                "type": "official",
            },
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/prati/?criterio=rilevanza&stato=ristrutturato",
        "recent_transactions": [
            {"address": "Via Cola di Rienzo", "price_m2": 8200, "surface": 95, "date": "2024-12", "type": "Gerenoveerd trilocale"},
            {"address": "Via Ottaviano", "price_m2": 7800, "surface": 110, "date": "2024-11", "type": "Gerenoveerd quadrilocale"},
            {"address": "Via Crescenzio", "price_m2": 8600, "surface": 85, "date": "2025-01", "type": "Gerenoveerd bilocale met terras"},
        ],
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
        "data_period": "H2 2024 – Q1 2025",
        "sources": [
            {
                "name": "Immobiliare.it Prijstrends Trieste",
                "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/trieste/",
                "type": "market_trend",
            },
            {
                "name": "OMI — Agenzia delle Entrate (Zone D5)",
                "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari",
                "type": "official",
            },
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/trieste/?criterio=rilevanza&stato=ristrutturato",
        "recent_transactions": [
            {"address": "Via Tagliamento", "price_m2": 6400, "surface": 120, "date": "2024-11", "type": "Gerenoveerd quadrilocale"},
            {"address": "Piazza Istria", "price_m2": 6800, "surface": 90, "date": "2024-12", "type": "Gerenoveerd trilocale"},
            {"address": "Via Salaria", "price_m2": 6100, "surface": 140, "date": "2025-01", "type": "Gerenoveerd penthouse"},
        ],
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
        "data_period": "H2 2024 – Q1 2025",
        "sources": [
            {
                "name": "Immobiliare.it Prijstrends Parioli",
                "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/parioli/",
                "type": "market_trend",
            },
            {
                "name": "OMI — Agenzia delle Entrate (Zone D1-D3)",
                "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari",
                "type": "official",
            },
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/parioli/?criterio=rilevanza&stato=ristrutturato",
        "recent_transactions": [
            {"address": "Viale Parioli", "price_m2": 7200, "surface": 130, "date": "2024-10", "type": "Gerenoveerd quadrilocale"},
            {"address": "Via Archimede", "price_m2": 8100, "surface": 100, "date": "2024-12", "type": "Gerenoveerd trilocale met balkon"},
            {"address": "Piazza Santiago del Cile", "price_m2": 7800, "surface": 160, "date": "2025-01", "type": "Gerenoveerde villa-etage"},
        ],
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
        "data_period": "H2 2024 – Q1 2025",
        "sources": [
            {
                "name": "Immobiliare.it Prijstrends Flaminio",
                "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/flaminio/",
                "type": "market_trend",
            },
            {
                "name": "OMI — Agenzia delle Entrate (Zone D4)",
                "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari",
                "type": "official",
            },
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/flaminio/?criterio=rilevanza&stato=ristrutturato",
        "recent_transactions": [
            {"address": "Viale del Vignola", "price_m2": 6900, "surface": 95, "date": "2024-11", "type": "Gerenoveerd trilocale"},
            {"address": "Via Flaminia", "price_m2": 7200, "surface": 80, "date": "2024-12", "type": "Gerenoveerd bilocale met terras"},
            {"address": "Piazza Gentile da Fabriano", "price_m2": 6500, "surface": 115, "date": "2025-02", "type": "Gerenoveerd quadrilocale"},
        ],
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
        "data_period": "H2 2024 – Q1 2025",
        "sources": [
            {
                "name": "Immobiliare.it Prijstrends Centro Storico",
                "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/centro/",
                "type": "market_trend",
            },
            {
                "name": "OMI — Agenzia delle Entrate (Zone B1-B8)",
                "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari",
                "type": "official",
            },
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/centro/?criterio=rilevanza&stato=ristrutturato",
        "recent_transactions": [
            {"address": "Via dei Coronari", "price_m2": 11500, "surface": 90, "date": "2024-10", "type": "Gerenoveerd trilocale"},
            {"address": "Rione Monti", "price_m2": 10800, "surface": 75, "date": "2024-12", "type": "Gerenoveerd bilocale met gewelven"},
            {"address": "Via Giulia", "price_m2": 13200, "surface": 120, "date": "2025-01", "type": "Palazzo-etage met fresco's"},
        ],
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
    "data_period": "H2 2024 – Q1 2025",
    "sources": [
        {
            "name": "Immobiliare.it Prijstrends Roma",
            "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/",
            "type": "market_trend",
        },
        {
            "name": "OMI — Agenzia delle Entrate",
            "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari",
            "type": "official",
        },
    ],
    "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/?criterio=rilevanza&stato=ristrutturato",
    "recent_transactions": [],
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
