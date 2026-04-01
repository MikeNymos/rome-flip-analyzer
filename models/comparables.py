"""
Comparable Market Analysis (CMA) engine.
Similarity scoring, batch-interne vergelijking, relatieve positionering,
verkoopsnelheid schatting en betrouwbaarheidsniveau.
"""
from __future__ import annotations

import statistics
from data.neighborhoods import get_neighborhood_benchmarks, ZONE_ALIASES


# ── SIMILARITY SCORE ──────────────────────────────────────

def calculate_similarity_score(target: dict, candidate: dict) -> float:
    """
    Bereken similarity score (0.0 – 1.0) tussen twee panden.

    Gewogen componenten:
        Wijk          30%
        Oppervlakte   25%
        Prijs/m2      15%
        Kamers        10%
        Verdieping    10%
        Staat          5%
        Gebouwtype     5%
    """
    score = 0.0

    # Wijk (30%)
    tz = _normalize_zone(target.get("zone", ""))
    cz = _normalize_zone(candidate.get("zone", ""))
    if tz == cz:
        score += 0.30
    elif _are_adjacent(tz, cz):
        score += 0.15

    # Oppervlakte (25%)
    ts = target.get("surface_m2", 0) or 1
    cs = candidate.get("surface_m2", 0)
    if cs:
        diff = abs(ts - cs) / ts
        if diff <= 0.40:
            score += 0.25 * (1 - diff / 0.40)

    # Prijs/m2 (15%)
    tp = target.get("price_per_m2", 0) or 1
    cp = candidate.get("price_per_m2", 0)
    if cp:
        diff = abs(tp - cp) / tp
        if diff <= 0.50:
            score += 0.15 * (1 - diff / 0.50)

    # Kamers (10%)
    tr = target.get("rooms")
    cr = candidate.get("rooms")
    if tr and cr:
        rd = abs(tr - cr)
        score += {0: 0.10, 1: 0.06, 2: 0.02}.get(rd, 0)
    else:
        score += 0.05

    # Verdieping (10%)
    tf = target.get("floor")
    cf = candidate.get("floor")
    if tf is not None and cf is not None:
        fd = abs(tf - cf)
        if fd == 0:
            score += 0.10
        elif fd <= 2:
            score += 0.06
        elif fd <= 4:
            score += 0.02
    else:
        score += 0.05

    # Staat (5%)
    tc = (target.get("condition") or "").lower()
    cc = (candidate.get("condition") or "").lower()
    if tc and cc:
        if tc == cc:
            score += 0.05
        elif _conditions_similar(tc, cc):
            score += 0.03
    else:
        score += 0.025

    # Gebouwtype (5%) — palazzo vs. normaal
    tp = _is_palazzo(target)
    cp = _is_palazzo(candidate)
    score += 0.05 if tp == cp else 0.02

    return round(score, 3)


# ── BATCH VERGELIJKING ────────────────────────────────────

def calculate_relative_position(listing: dict, all_listings: list[dict]) -> dict:
    """
    Bereken waar dit pand staat t.o.v. alle andere in de batch.
    """
    others = [l for l in all_listings if l.get("url") != listing.get("url")]
    if not others:
        return {"batch_rank": 1, "batch_total": 1, "batch_percentile": 50}

    same_zone = [l for l in others if _normalize_zone(l.get("zone", "")) == _normalize_zone(listing.get("zone", ""))]

    all_prices_m2 = sorted([l.get("price_per_m2", 0) for l in others if l.get("price_per_m2")])
    zone_prices_m2 = sorted([l.get("price_per_m2", 0) for l in same_zone if l.get("price_per_m2")])
    all_scores = sorted([l.get("flip_score", 0) for l in others])

    my_price_m2 = listing.get("price_per_m2", 0)
    my_score = listing.get("flip_score", 0)

    # Direct vergelijkbare panden (similarity >= 0.6)
    direct_comparables = []
    for other in others:
        sim = calculate_similarity_score(listing, other)
        if sim >= 0.6:
            direct_comparables.append({
                "zone": other.get("zone", "?"),
                "price": other.get("price", 0),
                "price_per_m2": other.get("price_per_m2", 0),
                "surface_m2": other.get("surface_m2", 0),
                "flip_score": other.get("flip_score", 0),
                "similarity": sim,
                "url": other.get("url", ""),
            })
    direct_comparables.sort(key=lambda x: x["similarity"], reverse=True)

    return {
        "batch_rank_price": _rank(my_price_m2, all_prices_m2),
        "batch_rank_score": _rank(my_score, all_scores, ascending=False),
        "batch_total": len(others) + 1,
        "batch_percentile_price": _percentile(my_price_m2, all_prices_m2),
        "batch_avg_price_m2": round(statistics.mean(all_prices_m2)) if all_prices_m2 else None,
        "batch_median_price_m2": round(statistics.median(all_prices_m2)) if all_prices_m2 else None,
        "batch_delta_pct": _delta_pct(my_price_m2, all_prices_m2),

        "zone_count": len(same_zone),
        "zone_avg_price_m2": round(statistics.mean(zone_prices_m2)) if zone_prices_m2 else None,
        "zone_delta_pct": _delta_pct(my_price_m2, zone_prices_m2),

        "direct_comparables": direct_comparables[:5],
        "direct_comparable_count": len(direct_comparables),
    }


# ── VERKOOPSNELHEID ───────────────────────────────────────

def estimate_selling_speed(listing: dict, analysis: dict, comparables: dict | None = None) -> dict:
    """
    Schat de verkoopsnelheid na renovatie in maanden.
    """
    nb = analysis.get("neighborhood_data") or {}
    base_months = nb.get("avg_selling_time_months", 4)
    adjustments: list[str] = []

    # Prijspositie t.o.v. markt
    sale_est = analysis.get("sale_price_estimate", {})
    our_m2 = sale_est.get("final_price_per_m2", {}).get("mid", 0)
    market_mid = nb.get("renovated_price_mid", our_m2 or 1)

    if market_mid:
        ratio = our_m2 / market_mid if market_mid else 1
        if ratio > 1.10:
            base_months += 2
            adjustments.append(f"+2 mnd: verkoopprijs {(ratio-1)*100:.0f}% boven marktgemiddelde")
        elif ratio > 1.05:
            base_months += 1
            adjustments.append("+1 mnd: verkoopprijs licht boven gemiddelde")
        elif ratio < 0.95:
            base_months -= 1
            adjustments.append("-1 mnd: agressieve pricing onder marktgemiddelde")

    # Concurrentie (via comparables)
    if comparables:
        n = comparables.get("direct_comparable_count", 0)
        if n > 10:
            base_months += 1
            adjustments.append(f"+1 mnd: hoge concurrentie ({n} vergelijkbare panden)")
        elif n < 3:
            base_months -= 0.5
            adjustments.append("-0.5 mnd: weinig directe concurrentie")

    # Pandkenmerken
    floor = listing.get("floor")
    if floor and floor >= 4 and listing.get("has_elevator"):
        base_months -= 0.5
        adjustments.append("-0.5 mnd: hoge verdieping met lift")

    desc = (listing.get("description") or "").lower()
    if any(kw in desc for kw in ["terrazzo", "terrazza", "terrace"]):
        base_months -= 0.5
        adjustments.append("-0.5 mnd: terras aanwezig")
    if any(kw in desc for kw in ["panoramico", "vista panoramica"]):
        base_months -= 0.5
        adjustments.append("-0.5 mnd: panoramisch uitzicht")

    est = max(1, round(base_months))

    if est <= 2:
        speed, desc_text = "SNEL", "Verwacht binnen 2 maanden verkocht"
    elif est <= 4:
        speed, desc_text = "NORMAAL", f"Verwacht binnen {est} maanden verkocht"
    else:
        speed, desc_text = "TRAAG", f"Verwacht {est}+ maanden op de markt"

    return {
        "estimated_months": est,
        "speed": speed,
        "speed_color": {"SNEL": "green", "NORMAAL": "orange", "TRAAG": "red"}[speed],
        "description": desc_text,
        "adjustments": adjustments,
    }


# ── BETROUWBAARHEIDSNIVEAU ────────────────────────────────

def calculate_confidence_level(comparables: dict | None = None) -> dict:
    """
    Bepaal hoe betrouwbaar de prijsschatting is op basis van
    beschikbaar vergelijkingsmateriaal.
    """
    score = 0
    factors: list[str] = []

    # Wijkbenchmarks (altijd beschikbaar)
    score += 20
    factors.append("Wijkbenchmarks beschikbaar (intern)")

    # Batch comparables
    if comparables:
        n = comparables.get("direct_comparable_count", 0)
        if n >= 5:
            score += 30
            factors.append(f"{n} vergelijkbare panden in batch (similarity >= 0.6)")
        elif n >= 2:
            score += 15
            factors.append(f"{n} vergelijkbare panden in batch")
        elif n >= 1:
            score += 5
            factors.append(f"Slechts {n} vergelijkbaar pand in batch")
        else:
            factors.append("Geen direct vergelijkbare panden in batch")
    else:
        factors.append("Batch-vergelijking niet beschikbaar")

    # Bepaal niveau
    if score >= 40:
        level, color = "HOOG", "green"
        explanation = "Voldoende vergelijkingsmateriaal voor betrouwbare schatting"
    elif score >= 25:
        level, color = "GEMIDDELD", "orange"
        explanation = "Beperkt vergelijkingsmateriaal — schatting is indicatief"
    else:
        level, color = "LAAG", "red"
        explanation = "Onvoldoende vergelijkingsmateriaal — schatting is een ruwe inschatting"

    return {
        "level": level,
        "score": score,
        "color": color,
        "explanation": explanation,
        "factors": factors,
    }


# ── HELPERS ───────────────────────────────────────────────

ADJACENT_ZONES = {
    "Prati": ["Flaminio", "Centro Storico", "Della Vittoria"],
    "Trieste": ["Parioli", "Salario", "Nomentano"],
    "Parioli": ["Trieste", "Flaminio"],
    "Flaminio": ["Prati", "Parioli"],
    "Centro Storico": ["Prati", "Trastevere"],
    "Trastevere": ["Centro Storico", "Testaccio"],
    "Testaccio": ["Trastevere", "Aventino", "Ostiense"],
    "San Giovanni": ["Esquilino", "Appio-Claudio"],
}


def _normalize_zone(zone: str) -> str:
    z = zone.strip().lower()
    return ZONE_ALIASES.get(z, zone.strip())


def _are_adjacent(a: str, b: str) -> bool:
    return b in ADJACENT_ZONES.get(a, []) or a in ADJACENT_ZONES.get(b, [])


_CONDITION_GROUPS = [
    {"da_ristrutturare", "da_rinnovare", "pessimo", "da ristrutturare"},
    {"buono", "abitabile", "discreto", "buono / abitabile"},
    {"ristrutturato", "ottimo", "nuovo", "ottimo / ristrutturato"},
]


def _conditions_similar(a: str, b: str) -> bool:
    for group in _CONDITION_GROUPS:
        if a in group and b in group:
            return True
    return False


def _is_palazzo(listing: dict) -> bool:
    text = f"{listing.get('title', '')} {listing.get('description', '')}".lower()
    return any(kw in text for kw in ["palazzo signorile", "palazzo d'epoca", "stabile signorile"])


def _rank(value: float, sorted_values: list[float], ascending: bool = True) -> int:
    """Rangpositie (1 = beste)."""
    if not sorted_values:
        return 1
    if ascending:
        return sum(1 for v in sorted_values if v < value) + 1
    return sum(1 for v in sorted_values if v > value) + 1


def _percentile(value: float, sorted_values: list[float]) -> float:
    if not sorted_values:
        return 50
    below = sum(1 for v in sorted_values if v <= value)
    return round(below / len(sorted_values) * 100, 1)


def _delta_pct(value: float, values: list[float]) -> float | None:
    if not values:
        return None
    median = statistics.median(values)
    if median == 0:
        return None
    return round((value - median) / median * 100, 1)
