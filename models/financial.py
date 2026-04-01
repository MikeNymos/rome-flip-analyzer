"""
Financieel berekeningsmodel voor vastgoedinvesteringen.
Berekent volledige P&L voor prima casa (hoofdscenario) en seconda casa (vergelijking).
"""
from __future__ import annotations

from data.neighborhoods import get_neighborhood_benchmarks
from models.location import assess_location_quality
from models.sale_price import estimate_sale_price


def calculate_investment_analysis(
    listing: dict,
    params: dict,
    overrides: dict | None = None,
) -> dict:
    """
    Berekent volledige investeringsanalyse voor een pand.

    Twee scenario's parallel:
    - PRIMA CASA (hoofdscenario): 2% belasting, onderhandelingskorting, geen plusvalenza
    - SECONDA CASA (vergelijking): 9% belasting, volle vraagprijs, 26% plusvalenza

    Args:
        listing: Genormaliseerd pand-dict met minimaal price, surface_m2, zone.
        params: Configureerbare parameters (uit config.DEFAULT_PARAMS).
        overrides: Optionele per-pand overschrijvingen voor renovatiekosten,
                   verkoopprijs, onderhandelingskorting.

    Returns:
        Dict met prima_casa, seconda_casa, midpoint_roi, sale_price_estimate,
        location_quality, en backward-compatibele aliassen.
    """
    if overrides is None:
        overrides = {}

    surface = listing["surface_m2"]
    price = listing["price"]

    # Haal benchmark- en analysedata op
    neighborhood_data = get_neighborhood_benchmarks(listing.get("zone", ""))
    location_quality = assess_location_quality(listing, neighborhood_data)
    sale_price_data = estimate_sale_price(listing, neighborhood_data, location_quality)

    # Per-pand verkoopprijsoverschrijving
    if overrides.get("sale_price_per_m2_mid"):
        sale_mid = overrides["sale_price_per_m2_mid"]
        sale_low = overrides.get("sale_price_per_m2_low", int(sale_mid * 0.88))
        sale_high = overrides.get("sale_price_per_m2_high", int(sale_mid * 1.12))
    else:
        sale_low = sale_price_data["final_price_per_m2"]["low"]
        sale_mid = sale_price_data["final_price_per_m2"]["mid"]
        sale_high = sale_price_data["final_price_per_m2"]["high"]

    # Per-pand renovatiekosten overschrijving
    reno_cost = overrides.get("renovation_cost_per_m2")
    reno_min = reno_cost or params["renovation_cost_min_per_m2"]
    reno_max = reno_cost or params["renovation_cost_max_per_m2"]

    # Per-pand onderhandelingskorting
    discount = overrides.get("asking_price_discount", params["asking_price_discount"])

    # === PRIMA CASA (HOOFDSCENARIO — 2% belasting) ===
    prima = {}
    prima["purchase_price"] = price * (1 - discount)
    prima["registration_tax"] = prima["purchase_price"] * params["registration_tax_prima_casa"]
    prima["notary"] = max(
        params["notary_cost_fixed"] * 0.85,
        prima["purchase_price"] * params["notary_cost_percentage"],
    )
    prima["broker_buy"] = prima["purchase_price"] * params["broker_buy_percentage"]
    prima["renovation"] = surface * reno_min
    prima["architect"] = max(
        params["architect_geometra_cost"] * 0.8,
        prima["renovation"] * params["architect_cost_percentage"],
    )
    prima["contingency"] = prima["renovation"] * params["contingency_percentage"] * 0.8
    prima["holding_costs"] = params["holding_cost_monthly"] * (params["project_duration_months"] - 2)
    prima["total_investment"] = sum([
        prima["purchase_price"],
        prima["registration_tax"],
        prima["notary"],
        prima["broker_buy"],
        prima["renovation"],
        prima["architect"],
        prima["contingency"],
        prima["holding_costs"],
    ])

    # Verkoopzijde prima casa
    prima["sale_price_per_m2"] = sale_mid
    prima["sale_price"] = surface * prima["sale_price_per_m2"]
    prima["broker_sell"] = prima["sale_price"] * params["broker_sell_percentage"]
    prima["plusvalenza_tax"] = 0  # Prima casa = GEEN meerwaardebelasting

    prima["net_revenue"] = prima["sale_price"] - prima["broker_sell"] - prima["plusvalenza_tax"]
    prima["net_profit"] = prima["net_revenue"] - prima["total_investment"]
    prima["roi"] = (prima["net_profit"] / prima["total_investment"]) * 100 if prima["total_investment"] > 0 else 0

    # === SECONDA CASA (VERGELIJKING — 9% belasting) ===
    seconda = {}
    seconda["purchase_price"] = price  # Geen korting in seconda casa
    seconda["registration_tax"] = seconda["purchase_price"] * params["registration_tax_seconda_casa"]
    seconda["notary"] = max(
        params["notary_cost_fixed"],
        seconda["purchase_price"] * params["notary_cost_percentage"],
    )
    seconda["broker_buy"] = seconda["purchase_price"] * params["broker_buy_percentage"]
    seconda["renovation"] = surface * reno_max
    seconda["architect"] = max(
        params["architect_geometra_cost"],
        seconda["renovation"] * params["architect_cost_percentage"],
    )
    seconda["contingency"] = seconda["renovation"] * params["contingency_percentage"]
    seconda["holding_costs"] = params["holding_cost_monthly"] * params["project_duration_months"]
    seconda["total_investment"] = sum([
        seconda["purchase_price"],
        seconda["registration_tax"],
        seconda["notary"],
        seconda["broker_buy"],
        seconda["renovation"],
        seconda["architect"],
        seconda["contingency"],
        seconda["holding_costs"],
    ])

    # Verkoopzijde seconda casa
    seconda["sale_price_per_m2"] = sale_low
    seconda["sale_price"] = surface * seconda["sale_price_per_m2"]
    seconda["broker_sell"] = seconda["sale_price"] * params["broker_sell_percentage"]

    # Plusvalenza seconda casa (26% meerwaardebelasting)
    seconda["documented_costs"] = seconda["total_investment"] - seconda["purchase_price"]
    seconda["capital_gain"] = seconda["sale_price"] - seconda["purchase_price"] - seconda["documented_costs"]
    seconda["plusvalenza_tax"] = max(0, seconda["capital_gain"] * params["plusvalenza_rate"])

    seconda["net_revenue"] = seconda["sale_price"] - seconda["broker_sell"] - seconda["plusvalenza_tax"]
    seconda["net_profit"] = seconda["net_revenue"] - seconda["total_investment"]
    seconda["roi"] = (seconda["net_profit"] / seconda["total_investment"]) * 100 if seconda["total_investment"] > 0 else 0

    return {
        "prima_casa": prima,
        "seconda_casa": seconda,
        # Backward-compatibele aliassen
        "conservative": seconda,
        "optimistic": prima,
        "midpoint_roi": (prima["roi"] + seconda["roi"]) / 2,
        "neighborhood_data": neighborhood_data,
        "sale_price_estimate": sale_price_data,
        "location_quality": location_quality,
    }


def calculate_sensitivity(
    listing: dict,
    params: dict,
    overrides: dict | None = None,
) -> list[dict]:
    """
    Gevoeligheidsanalyse: wat-als scenario's.
    """
    base = calculate_investment_analysis(listing, params, overrides)
    scenarios = []

    # Scenario 1: Aankoopprijs 10% lager
    mod_listing = listing.copy()
    mod_listing["price"] = listing["price"] * 0.90
    result = calculate_investment_analysis(mod_listing, params, overrides)
    scenarios.append({
        "scenario": "Aankoopprijs 10% lager",
        "midpoint_roi": result["midpoint_roi"],
        "prima_profit": result["prima_casa"]["net_profit"],
        "seconda_profit": result["seconda_casa"]["net_profit"],
        "delta_roi": result["midpoint_roi"] - base["midpoint_roi"],
    })

    # Scenario 2: Renovatie 20% duurder
    mod_overrides = dict(overrides or {})
    base_reno = mod_overrides.get("renovation_cost_per_m2")
    if base_reno:
        mod_overrides["renovation_cost_per_m2"] = int(base_reno * 1.20)
    else:
        mod_params = params.copy()
        mod_params["renovation_cost_max_per_m2"] = params["renovation_cost_max_per_m2"] * 1.20
        mod_params["renovation_cost_min_per_m2"] = params["renovation_cost_min_per_m2"] * 1.20
        result = calculate_investment_analysis(listing, mod_params, overrides)
        scenarios.append({
            "scenario": "Renovatie 20% duurder",
            "midpoint_roi": result["midpoint_roi"],
            "prima_profit": result["prima_casa"]["net_profit"],
            "seconda_profit": result["seconda_casa"]["net_profit"],
            "delta_roi": result["midpoint_roi"] - base["midpoint_roi"],
        })
        mod_overrides = None  # skip the override path

    if mod_overrides is not None:
        result = calculate_investment_analysis(listing, params, mod_overrides)
        scenarios.append({
            "scenario": "Renovatie 20% duurder",
            "midpoint_roi": result["midpoint_roi"],
            "prima_profit": result["prima_casa"]["net_profit"],
            "seconda_profit": result["seconda_casa"]["net_profit"],
            "delta_roi": result["midpoint_roi"] - base["midpoint_roi"],
        })

    # Scenario 3: Verkoopprijs 10% lager
    prima = base["prima_casa"]
    seconda = base["seconda_casa"]
    p_sale = prima["sale_price"] * 0.90
    p_broker = p_sale * params["broker_sell_percentage"]
    p_profit = p_sale - p_broker - prima["total_investment"]
    p_roi = (p_profit / prima["total_investment"]) * 100

    s_sale = seconda["sale_price"] * 0.90
    s_broker = s_sale * params["broker_sell_percentage"]
    s_gain = s_sale - seconda["purchase_price"] - seconda["documented_costs"]
    s_tax = max(0, s_gain * params["plusvalenza_rate"])
    s_profit = s_sale - s_broker - s_tax - seconda["total_investment"]
    s_roi = (s_profit / seconda["total_investment"]) * 100

    mid_roi = (p_roi + s_roi) / 2
    scenarios.append({
        "scenario": "Verkoopprijs 10% lager",
        "midpoint_roi": mid_roi,
        "prima_profit": p_profit,
        "seconda_profit": s_profit,
        "delta_roi": mid_roi - base["midpoint_roi"],
    })

    # Scenario 4: Projectduur +4 maanden
    mod_params4 = params.copy()
    mod_params4["project_duration_months"] = params["project_duration_months"] + 4
    result = calculate_investment_analysis(listing, mod_params4, overrides)
    scenarios.append({
        "scenario": "Projectduur +4 maanden",
        "midpoint_roi": result["midpoint_roi"],
        "prima_profit": result["prima_casa"]["net_profit"],
        "seconda_profit": result["seconda_casa"]["net_profit"],
        "delta_roi": result["midpoint_roi"] - base["midpoint_roi"],
    })

    return scenarios
