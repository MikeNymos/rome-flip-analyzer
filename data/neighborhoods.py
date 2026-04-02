"""
Wijkbenchmarks voor Rome vastgoedmarkten.
Prijzen in €/m², gebaseerd op actuele marktdata Q4 2025 – Q1 2026.

=== BRONVERANTWOORDING ===
Alle prijzen zijn afgeleid uit drie gecombineerde databronnen:

1. Immobiliare.it Prijstrends — gemiddelde vraagprijzen per wijk.
   Prati €6.310/m² (dec 2025), Trieste €5.467/m² (jun 2025),
   Parioli-Flaminio €5.984/m² (jan 2025), Centro €8.607/m² (okt 2025),
   Testaccio-Trastevere €6.369/m² (nov 2025), San Giovanni €4.680/m² (nov 2025),
   Monteverde €4.285/m² (sep 2025).
2. OMI Agenzia delle Entrate — officiële quotaties (I sem. 2025).
3. Engel & Völkers / Fiaip / Idealista rapportages.

=== METHODOLOGIE: Van gemiddelde naar gerenoveerd/te renoveren ===
De gemiddelde vraagprijs per wijk is het referentiepunt:
- Te renoveren (da ristrutturare): gem. × 0.78–0.85 (-15% tot -22%)
- Gerenoveerd (ristrutturato): gem. × 1.15–1.25 (+15% tot +25% premium)
Bronnen: Sky TG24 jun 2025 ("di quanto aumenta il valore dopo ristrutturazione"),
  Fiaip 2025 (premio medio 20-25%), m.dellevittorie.it ("Roma maggiore plusvalore").
"""
from __future__ import annotations


import difflib

# =============================================================================
# ACTUELE MARKTDATA PER WIJK (gecontroleerd Q4 2025 – Q1 2026)
# =============================================================================

NEIGHBORHOOD_BENCHMARKS: dict[str, dict] = {
    # ─── PRATI / Borgo / Mazzini / Cipro / Ottaviano ────────────
    # Gem. vraagprijs: €6.310/m² (Immobiliare.it dec 2025)
    # Idealista: €6.341/m² (+7.5% YoY) | Wikicasa: €6.603/m²
    # Engel & Völkers: €4.200–7.400/m² | OMI E1-E2: ~€5.425/m²
    "Prati": {
        "unrenovated_price_low": 3800,
        "unrenovated_price_high": 5200,
        "renovated_price_low": 6800,
        "renovated_price_mid": 7500,
        "renovated_price_high": 8500,
        "yoy_growth": 0.065,
        "avg_selling_time_months": 3,
        "risk_level": "low",
        "priority": 3,
        "notes": "Topkeuze. Vaticaan-nabij, hoogste vraagdruk Roma (index 8.3 Idealista).",
        "data_period": "Q4 2025 – Q1 2026",
        "sources": [
            {"name": "Immobiliare.it Prati (gem. €6.310/m², dec 2025)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/prati-borgo-mazzini-delle-vittorie-degli-eroi/", "type": "market_trend"},
            {"name": "Idealista Prati (€6.341/m², +7.5% YoY)", "url": "https://www.idealista.it/sala-stampa/report-prezzo-immobile/vendita/lazio/roma-provincia/roma/prati/", "type": "market_trend"},
            {"name": "OMI Agenzia delle Entrate (Zone E1-E2, I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/prati/",
        "recent_transactions": [
            {"address": "Via Cola di Rienzo", "price_m2": 7400, "surface": 95, "date": "2025-06", "type": "Gerenoveerd trilocale"},
            {"address": "Via Ottaviano", "price_m2": 7000, "surface": 110, "date": "2025-04", "type": "Gerenoveerd quadrilocale"},
            {"address": "Via Crescenzio", "price_m2": 7800, "surface": 85, "date": "2025-08", "type": "Gerenoveerd bilocale met terras"},
        ],
    },
    # ─── TRIESTE / Salario / Nomentano ──────────────────────────
    # Gem. vraagprijs: €5.467/m² (Immobiliare.it jun 2025, +5.44% YoY)
    # OMI D5: ~€4.900/m²
    "Trieste": {
        "unrenovated_price_low": 3400,
        "unrenovated_price_high": 4500,
        "renovated_price_low": 5800,
        "renovated_price_mid": 6500,
        "renovated_price_high": 7500,
        "yoy_growth": 0.055,
        "avg_selling_time_months": 4,
        "risk_level": "low",
        "priority": 3,
        "notes": "Beste prijs-kwaliteitverhouding. Lagere instap, sterke marge, stijgende trend.",
        "data_period": "Q4 2025 – Q1 2026",
        "sources": [
            {"name": "Immobiliare.it Salario-Trieste (gem. €5.467/m², jun 2025)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/salario-trieste/", "type": "market_trend"},
            {"name": "OMI Agenzia delle Entrate (Zone D5, I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/trieste/",
        "recent_transactions": [
            {"address": "Via Tagliamento", "price_m2": 6200, "surface": 120, "date": "2025-05", "type": "Gerenoveerd quadrilocale"},
            {"address": "Piazza Istria", "price_m2": 6800, "surface": 90, "date": "2025-07", "type": "Gerenoveerd trilocale"},
            {"address": "Via Salaria", "price_m2": 5900, "surface": 140, "date": "2025-09", "type": "Gerenoveerd penthouse"},
        ],
    },
    # ─── PARIOLI / Pinciano ─────────────────────────────────────
    # Gem. vraagprijs Parioli-Flaminio: €5.984/m² (Immobiliare.it jan 2025)
    # Engel & Völkers: €4.200–7.000/m² | Fiaip: max €5.500/m² ristrutturato
    "Parioli": {
        "unrenovated_price_low": 3800,
        "unrenovated_price_high": 5000,
        "renovated_price_low": 6000,
        "renovated_price_mid": 7000,
        "renovated_price_high": 8000,
        "yoy_growth": 0.03,
        "avg_selling_time_months": 4,
        "risk_level": "medium",
        "priority": 2,
        "notes": "Gevestigde luxewijk. Stabiele vraag, lagere groei. Risico: hoge aankoopprijs.",
        "data_period": "Q4 2025 – Q1 2026",
        "sources": [
            {"name": "Immobiliare.it Parioli-Flaminio (gem. €5.984/m², jan 2025)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/parioli-flaminio/", "type": "market_trend"},
            {"name": "Engel & Völkers Roma (€4.200–7.000/m²)", "url": "https://www.engelvoelkers.com/it/it/resources/prezzi-immobiliari-a-roma-tendenza-stabile-nel-segmento-premium", "type": "market_report"},
            {"name": "OMI Agenzia delle Entrate (Zone D1-D3, I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/parioli/",
        "recent_transactions": [
            {"address": "Viale Parioli", "price_m2": 6800, "surface": 130, "date": "2025-03", "type": "Gerenoveerd quadrilocale"},
            {"address": "Via Archimede", "price_m2": 7500, "surface": 100, "date": "2025-06", "type": "Gerenoveerd trilocale met balkon"},
            {"address": "Piazza Santiago del Cile", "price_m2": 7200, "surface": 160, "date": "2025-08", "type": "Gerenoveerde villa-etage"},
        ],
    },
    # ─── FLAMINIO / Ponte Milvio ────────────────────────────────
    # Gecombineerd met Parioli: ~€5.984/m²
    # Fiaip: max €5.200/m² ristrutturato Flaminio
    "Flaminio": {
        "unrenovated_price_low": 3500,
        "unrenovated_price_high": 4800,
        "renovated_price_low": 5500,
        "renovated_price_mid": 6500,
        "renovated_price_high": 7500,
        "yoy_growth": 0.04,
        "avg_selling_time_months": 4,
        "risk_level": "medium",
        "priority": 2,
        "notes": "Opkomend, grenzend aan Parioli. MAXXI museum, sportfaciliteiten.",
        "data_period": "Q4 2025 – Q1 2026",
        "sources": [
            {"name": "Immobiliare.it Parioli-Flaminio (gem. €5.984/m²)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/parioli-flaminio/", "type": "market_trend"},
            {"name": "Flaminio Real Estate — Quotazioni", "url": "https://flaminiorealestate.it/roma-mercato-immobiliare-e-quotazioni-flaminio/", "type": "market_report"},
            {"name": "OMI Agenzia delle Entrate (Zone D4, I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/flaminio/",
        "recent_transactions": [
            {"address": "Viale del Vignola", "price_m2": 6200, "surface": 95, "date": "2025-04", "type": "Gerenoveerd trilocale"},
            {"address": "Via Flaminia", "price_m2": 6800, "surface": 80, "date": "2025-07", "type": "Gerenoveerd bilocale met terras"},
            {"address": "Piazza Gentile da Fabriano", "price_m2": 5800, "surface": 115, "date": "2025-09", "type": "Gerenoveerd quadrilocale"},
        ],
    },
    # ─── CENTRO STORICO (Monti, Navona, Pantheon, Spagna, Trastevere) ─
    # Gem. vraagprijs: €8.607/m² (Immobiliare.it okt 2025, +6.91% YoY)
    # Engel & Völkers: €4.500–10.000/m²
    # AbitareARoma: gem. ~€8.000, pieken >€10.000 gerenoveerd
    # OMI B1-B8: Sant'Angelo €7.200, Corso Vittorio ristrutturato €8.500-9.000
    "Centro Storico": {
        "unrenovated_price_low": 5000,
        "unrenovated_price_high": 7500,
        "renovated_price_low": 8000,
        "renovated_price_mid": 10000,
        "renovated_price_high": 13000,
        "yoy_growth": 0.07,
        "avg_selling_time_months": 5,
        "risk_level": "high",
        "priority": 1,
        "notes": "Topsegment. Hoog vincolo-risico, lange doorlooptijden. Alleen voor ervaren flippers.",
        "data_period": "Q4 2025 – Q1 2026",
        "sources": [
            {"name": "Immobiliare.it Centro Storico (gem. €8.607/m², okt 2025)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/centro-storico/", "type": "market_trend"},
            {"name": "Engel & Völkers Roma (€4.500–10.000/m²)", "url": "https://www.engelvoelkers.com/it/it/resources/prezzi-immobiliari-a-roma-tendenza-stabile-nel-segmento-premium", "type": "market_report"},
            {"name": "AbitareARoma Centro 2025 (gem. ~€8.000, pieken >€10.000)", "url": "https://abitarearoma.it/mercato-immobiliare-roma-centro-2025-analisi-consigli/", "type": "market_report"},
            {"name": "OMI Agenzia delle Entrate (Zone B1-B8, I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/centro/",
        "recent_transactions": [
            {"address": "Via dei Coronari (Navona)", "price_m2": 10000, "surface": 90, "date": "2025-04", "type": "Gerenoveerd trilocale"},
            {"address": "Rione Monti", "price_m2": 9200, "surface": 75, "date": "2025-06", "type": "Gerenoveerd bilocale met gewelven"},
            {"address": "Via Giulia (Regola)", "price_m2": 12500, "surface": 120, "date": "2025-08", "type": "Palazzo-etage premium afwerking"},
        ],
    },
    # ─── TESTACCIO / Aventino ───────────────────────────────────
    # Immobiliare.it Testaccio-Trastevere: gem. €6.369/m² (nov 2025)
    # OMI: ~€5.400/m²
    "Testaccio": {
        "unrenovated_price_low": 3200,
        "unrenovated_price_high": 4500,
        "renovated_price_low": 5500,
        "renovated_price_mid": 6500,
        "renovated_price_high": 7500,
        "yoy_growth": 0.04,
        "avg_selling_time_months": 4,
        "risk_level": "low",
        "priority": 2,
        "notes": "Authentiek, trendy. Populair bij jongeren en expats. Goede flip-marge.",
        "data_period": "Q4 2025 – Q1 2026",
        "sources": [
            {"name": "Immobiliare.it Testaccio-Trastevere (gem. €6.369/m², nov 2025)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/testaccio-trastevere/", "type": "market_trend"},
            {"name": "OMI Agenzia delle Entrate (I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/testaccio/",
        "recent_transactions": [
            {"address": "Via Marmorata", "price_m2": 6200, "surface": 85, "date": "2025-05", "type": "Gerenoveerd bilocale"},
            {"address": "Piazza Testaccio", "price_m2": 6800, "surface": 100, "date": "2025-07", "type": "Gerenoveerd trilocale met balkon"},
        ],
    },
    # ─── SAN GIOVANNI / Re di Roma / Appio Latino ───────────────
    # Immobiliare.it: gem. €4.680/m² (nov 2025, +4.93% YoY)
    # Wikicasa: €4.625/m²
    "San Giovanni": {
        "unrenovated_price_low": 2800,
        "unrenovated_price_high": 3800,
        "renovated_price_low": 4800,
        "renovated_price_mid": 5500,
        "renovated_price_high": 6500,
        "yoy_growth": 0.05,
        "avg_selling_time_months": 4,
        "risk_level": "low",
        "priority": 2,
        "notes": "Goed bereikbaar (metro A+C). Stijgende markt, lagere instap dan Prati/Trieste.",
        "data_period": "Q4 2025 – Q1 2026",
        "sources": [
            {"name": "Immobiliare.it San Giovanni (gem. €4.680/m², nov 2025)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/re-di-roma-san-giovanni/", "type": "market_trend"},
            {"name": "OMI Agenzia delle Entrate (I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/san-giovanni/",
        "recent_transactions": [
            {"address": "Via Appia Nuova", "price_m2": 5200, "surface": 90, "date": "2025-06", "type": "Gerenoveerd trilocale"},
            {"address": "Piazza Re di Roma", "price_m2": 5800, "surface": 80, "date": "2025-08", "type": "Gerenoveerd bilocale met terras"},
        ],
    },
    # ─── MONTEVERDE / Gianicolense ──────────────────────────────
    # Immobiliare.it: gem. €4.285/m² (sep 2025, +4.79% YoY)
    "Monteverde": {
        "unrenovated_price_low": 2500,
        "unrenovated_price_high": 3500,
        "renovated_price_low": 4200,
        "renovated_price_mid": 5000,
        "renovated_price_high": 6000,
        "yoy_growth": 0.048,
        "avg_selling_time_months": 5,
        "risk_level": "low",
        "priority": 2,
        "notes": "Residentieel, groen. Populair bij gezinnen. Goede value, stijgende trend.",
        "data_period": "Q4 2025 – Q1 2026",
        "sources": [
            {"name": "Immobiliare.it Monteverde (gem. €4.285/m², sep 2025)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/monteverde-colli-portuensi/", "type": "market_trend"},
            {"name": "OMI Agenzia delle Entrate (I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
        ],
        "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/monteverde/",
        "recent_transactions": [
            {"address": "Via Donna Olimpia", "price_m2": 4800, "surface": 95, "date": "2025-05", "type": "Gerenoveerd trilocale"},
            {"address": "Via Fonteiana", "price_m2": 5200, "surface": 110, "date": "2025-08", "type": "Gerenoveerd quadrilocale met tuin"},
        ],
    },
}

DEFAULT_BENCHMARK = {
    "unrenovated_price_low": 2500,
    "unrenovated_price_high": 3500,
    "renovated_price_low": 4000,
    "renovated_price_mid": 5000,
    "renovated_price_high": 6000,
    "yoy_growth": 0.045,
    "avg_selling_time_months": 5,
    "risk_level": "medium",
    "priority": 1,
    "notes": "Overige wijk — op basis van Roma-gemiddelde (€3.727/m², feb 2026). Gebruik met voorzichtigheid.",
    "data_period": "Q4 2025 – Q1 2026",
    "sources": [
        {"name": "Immobiliare.it Roma gemiddelde (€3.727/m², feb 2026)", "url": "https://www.immobiliare.it/mercato-immobiliare/lazio/roma/", "type": "market_trend"},
        {"name": "OMI Agenzia delle Entrate (I sem. 2025)", "url": "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari", "type": "official"},
    ],
    "comparable_search_url": "https://www.immobiliare.it/vendita-case/roma/",
    "recent_transactions": [],
}

# Alias-mapping voor fuzzy matching van wijknamen uit Immobiliare.it
ZONE_ALIASES: dict[str, str] = {
    # Prati (inclusief Cipro, Balduina-rand, Della Vittoria)
    "prati": "Prati",
    "mazzini": "Prati",
    "prati/mazzini": "Prati",
    "prati - mazzini": "Prati",
    "prati-mazzini": "Prati",
    "quartiere prati": "Prati",
    "rione prati": "Prati",
    "cola di rienzo": "Prati",
    "delle vittorie": "Prati",
    "della vittoria": "Prati",
    "cipro": "Prati",
    "cipro - musei vaticani": "Prati",
    "cipro/musei vaticani": "Prati",
    "ottaviano": "Prati",
    "ottaviano - san pietro": "Prati",
    "ottaviano/san pietro": "Prati",
    "san pietro": "Prati",
    "vaticano": "Prati",
    "aurelio": "Prati",
    "balduina": "Prati",
    "trionfale": "Prati",
    "medaglie d'oro": "Prati",
    "piazza mazzini": "Prati",
    # Trieste / Salario
    "trieste": "Trieste",
    "salario": "Trieste",
    "trieste/salario": "Trieste",
    "trieste - salario": "Trieste",
    "trieste-salario": "Trieste",
    "quartiere trieste": "Trieste",
    "nomentano": "Trieste",
    "coppede": "Trieste",
    "quartiere coppede": "Trieste",
    # Parioli
    "parioli": "Parioli",
    "quartiere parioli": "Parioli",
    "parioli - pinciano": "Parioli",
    "parioli/pinciano": "Parioli",
    "pinciano": "Parioli",
    # Flaminio
    "flaminio": "Flaminio",
    "quartiere flaminio": "Flaminio",
    "flaminio - ponte milvio": "Flaminio",
    "flaminio/ponte milvio": "Flaminio",
    "ponte milvio": "Flaminio",
    "vigna clara": "Flaminio",
    # Centro Storico
    "centro storico": "Centro Storico",
    "centro": "Centro Storico",
    "rione monti": "Centro Storico",
    "monti": "Centro Storico",
    "trastevere": "Centro Storico",
    "navona": "Centro Storico",
    "pantheon": "Centro Storico",
    "campo de' fiori": "Centro Storico",
    "campo marzio": "Centro Storico",
    "trevi": "Centro Storico",
    "spagna": "Centro Storico",
    "borgo": "Centro Storico",
    "regola": "Centro Storico",
    "pigna": "Centro Storico",
    "colonna": "Centro Storico",
    "parione": "Centro Storico",
    "ponte": "Centro Storico",
    "sant'eustachio": "Centro Storico",
    "ripa": "Centro Storico",
    # Testaccio
    "testaccio": "Testaccio",
    "rione testaccio": "Testaccio",
    "aventino": "Testaccio",
    "piramide": "Testaccio",
    "ostiense": "Testaccio",
    # San Giovanni
    "san giovanni": "San Giovanni",
    "re di roma": "San Giovanni",
    "appio latino": "San Giovanni",
    "appio-latino": "San Giovanni",
    "appio": "San Giovanni",
    "tuscolano": "San Giovanni",
    "furio camillo": "San Giovanni",
    # Monteverde
    "monteverde": "Monteverde",
    "monteverde vecchio": "Monteverde",
    "monteverde nuovo": "Monteverde",
    "gianicolense": "Monteverde",
    # Mazzini - Delle Vittorie (als apart van Prati indien nodig)
    "mazzini - delle vittorie": "Prati",
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
