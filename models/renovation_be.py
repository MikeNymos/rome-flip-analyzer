"""
Renovatiekostschatting voor Belgische panden.
3 niveaus: opfrisbeurt, lichte renovatie, zware renovatie.
Met correctiefactoren voor EPC, bouwjaar, oppervlakte, lift.
"""
from __future__ import annotations

from data.constants_be import CONDITION_MAP_BE, RENOVATION_LEVELS


def estimate_renovation_cost(listing: dict, params: dict) -> dict:
    """
    Schat de totale renovatiekost op basis van pandkenmerken.

    Returns:
        dict met: level, base_cost_m2, adjusted_cost_m2, corrections[],
                  total_base, interior_architect, contingency, total_cost,
                  project_duration_months
    """
    condition = listing.get("condition", "TO_BE_DONE_UP")
    level_key = CONDITION_MAP_BE.get(condition, "lichte_renovatie")

    if level_key == "buiten_scope":
        return {
            "level": "buiten_scope",
            "level_label": "Buiten scope (vergunningsplichtig)",
            "base_cost_m2": 0,
            "adjusted_cost_m2": 0,
            "corrections": [],
            "total_base": 0,
            "interior_architect": 0,
            "contingency": 0,
            "total_cost": 0,
            "project_duration_months": 0,
            "is_excluded": True,
            "exclusion_reason": "Vergunningsplichtig — structurele ingrepen vereist",
        }

    level = RENOVATION_LEVELS[level_key]
    living_area = listing.get("living_area", listing.get("surface_m2", 80))
    base_cost_m2 = level["cost_mid"]

    if level_key == "geen_renovatie":
        return {
            "level": level_key,
            "level_label": level["label"],
            "base_cost_m2": 0,
            "adjusted_cost_m2": 0,
            "corrections": [],
            "total_base": 0,
            "interior_architect": 0,
            "contingency": 0,
            "total_cost": 0,
            "project_duration_months": level["total_project_months"],
            "is_excluded": False,
        }

    corrections = []
    additive_extra = 0
    multiplicative_factor = 1.0

    # ─── EPC correcties ─────────────────────────────────────
    epc = listing.get("epc_score", "")
    epc_value = listing.get("epc_value")

    if epc in ("F", "G") or (epc_value and epc_value > 400):
        additive_extra += 150
        corrections.append({
            "name": f"EPC {epc or 'F/G'} (kWh > 400)",
            "impact": "+€150/m²",
            "type": "additief",
        })
    elif epc == "E" or (epc_value and 300 <= epc_value <= 400):
        additive_extra += 75
        corrections.append({
            "name": f"EPC {epc or 'E'} (kWh 300-400)",
            "impact": "+€75/m²",
            "type": "additief",
        })

    # ─── Bouwjaar correcties ────────────────────────────────
    year = listing.get("construction_year")
    if year and year < 1950:
        additive_extra += 100
        corrections.append({
            "name": f"Bouwjaar {year} (< 1950)",
            "impact": "+€100/m²",
            "type": "additief",
        })
    elif year and 1950 <= year <= 1980:
        additive_extra += 50
        corrections.append({
            "name": f"Bouwjaar {year} (1950-1980)",
            "impact": "+€50/m²",
            "type": "additief",
        })

    # ─── Lift correctie ─────────────────────────────────────
    floor = listing.get("floor")
    has_lift = listing.get("has_lift", False)
    if not has_lift and floor is not None and floor >= 3:
        additive_extra += 30
        corrections.append({
            "name": f"Geen lift + verdieping {floor}",
            "impact": "+€30/m²",
            "type": "additief",
        })

    # ─── Oppervlakte correcties ─────────────────────────────
    if living_area > 200:
        multiplicative_factor *= 0.90
        corrections.append({
            "name": f"Grote oppervlakte ({living_area:.0f}m²)",
            "impact": "×0.90 (schaalvoordeel)",
            "type": "multiplicatief",
        })
    elif living_area < 60:
        multiplicative_factor *= 1.10
        corrections.append({
            "name": f"Kleine oppervlakte ({living_area:.0f}m²)",
            "impact": "×1.10 (hogere kosten per m²)",
            "type": "multiplicatief",
        })

    # ─── Berekening ─────────────────────────────────────────
    adjusted_cost_m2 = (base_cost_m2 + additive_extra) * multiplicative_factor
    total_base = round(living_area * adjusted_cost_m2)

    interior_architect = params.get("interior_architect_cost", 2000)
    contingency_pct = params.get("contingency_pct", 0.10)
    contingency = round(total_base * contingency_pct)

    total_cost = total_base + interior_architect + contingency

    return {
        "level": level_key,
        "level_label": level["label"],
        "base_cost_m2": base_cost_m2,
        "adjusted_cost_m2": round(adjusted_cost_m2),
        "corrections": corrections,
        "total_base": total_base,
        "interior_architect": interior_architect,
        "contingency": contingency,
        "total_cost": total_cost,
        "project_duration_months": level["total_project_months"],
        "is_excluded": False,
    }
