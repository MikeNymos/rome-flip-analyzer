"""
Financieel model voor Belgische vastgoedinvesteringen.
BV-structuur: bruto winst vóór vennootschapsbelasting.
Registratierechten 6% (beroepsverkoper Vlaanderen).
"""
from __future__ import annotations

from data.constants_be import calculate_notary_cost_simple, REGISTRATION_TAX_RATES
from models.renovation_be import estimate_renovation_cost
from models.sale_price_be import estimate_arv


def calculate_investment_analysis_be(listing: dict, params: dict,
                                      overrides: dict | None = None) -> dict:
    """
    Volledige P&L berekening voor een Belgisch vastgoedpand.

    Eén scenario: BV, bruto winst vóór vennootschapsbelasting.
    Registratierechten beroepsverkoper (6% Vlaanderen / 8% Brussel / 5% Wallonië).

    Returns:
        dict met: aankoopzijde, verkoopzijde, P&L totalen,
                  renovation_estimate, arv_estimate, projectduur
    """
    # === INPUTS ===
    price = listing.get("price", 0)
    living_area = listing.get("living_area", listing.get("surface_m2", 80))
    prop_type = listing.get("property_type", "APARTMENT")
    is_apartment = prop_type not in ("HOUSE", "HOUSE_ROW", "HOUSE_SEMI", "HOUSE_DETACHED", "VILLA")

    negotiation_margin = params.get("negotiation_margin", 0.05)
    region = params.get("region", "VLAANDEREN")
    ltv = params.get("ltv", 0.80)
    interest_rate = params.get("interest_rate", 0.045)
    agent_sell_pct = params.get("agent_sell_pct", 0.03)
    agent_buy_pct = params.get("agent_buy_pct", 0.00)

    # Overrides (per-pand sliders)
    if overrides:
        if "renovation_cost_m2" in overrides:
            listing = {**listing, "_reno_override": overrides["renovation_cost_m2"]}
        if "arv_m2" in overrides:
            pass  # handled below
        if "negotiation_margin" in overrides:
            negotiation_margin = overrides["negotiation_margin"]

    # === RENOVATIESCHATTING ===
    reno = estimate_renovation_cost(listing, params)
    if reno.get("is_excluded"):
        return _excluded_result(listing, reno)

    # Override renovatiekosten als slider is aangepast
    if overrides and "renovation_cost_m2" in overrides:
        reno_cost_m2 = overrides["renovation_cost_m2"]
        total_base = round(living_area * reno_cost_m2)
        contingency = round(total_base * params.get("contingency_pct", 0.10))
        reno["total_base"] = total_base
        reno["contingency"] = contingency
        reno["total_cost"] = total_base + reno["interior_architect"] + contingency
        reno["adjusted_cost_m2"] = reno_cost_m2

    # === ARV SCHATTING ===
    arv_data = estimate_arv(listing, params)
    arv_mid = arv_data["arv"]["mid"]

    # Override ARV als slider is aangepast
    if overrides and "arv_m2" in overrides:
        arv_m2 = overrides["arv_m2"]
        arv_mid = round(arv_m2 * living_area)
        arv_data["arv"]["mid"] = arv_mid
        arv_data["arv"]["low"] = round(arv_m2 * 0.90 * living_area)
        arv_data["arv"]["high"] = round(arv_m2 * 1.10 * living_area)
        arv_data["arv_per_m2"]["mid"] = arv_m2

    # === AANKOOPZIJDE ===
    purchase_price = round(price * (1 - negotiation_margin))
    reg_tax_rate = REGISTRATION_TAX_RATES.get(region, 0.06)
    registration_tax = round(purchase_price * reg_tax_rate)
    notary_buy = calculate_notary_cost_simple(purchase_price)
    mortgage_inscription = round((purchase_price * ltv * 0.01) + 500) if ltv > 0 else 0
    broker_buy = round(purchase_price * agent_buy_pct) if agent_buy_pct > 0 else 0

    renovation_cost = reno["total_cost"]
    project_months = reno["project_duration_months"]

    # Holding costs
    holding_monthly = params.get("holding_cost_apt", 500) if is_apartment else params.get("holding_cost_house", 350)
    holding_costs = round(holding_monthly * project_months)

    # Financieringskosten (interest op lening)
    financing_costs = round((purchase_price * ltv * interest_rate * project_months) / 12)

    total_investment = (
        purchase_price + registration_tax + notary_buy +
        mortgage_inscription + broker_buy + renovation_cost +
        holding_costs + financing_costs
    )

    # === VERKOOPZIJDE ===
    agent_sell_effective = agent_sell_pct * 1.21  # +21% BTW
    broker_sell = round(arv_mid * agent_sell_effective)
    notary_sell = 1500  # vast bedrag

    net_sale_price = arv_mid - broker_sell - notary_sell

    # === WINST ===
    gross_profit = net_sale_price - total_investment
    roi = (gross_profit / total_investment * 100) if total_investment > 0 else 0

    # === BREAK-EVEN ===
    break_even_arv = round((total_investment + 1500) / (1 - agent_sell_effective))

    return {
        # Aankoopzijde
        "purchase_price": purchase_price,
        "original_price": price,
        "negotiation_margin": negotiation_margin,
        "registration_tax": registration_tax,
        "registration_tax_rate": reg_tax_rate,
        "notary_buy": notary_buy,
        "mortgage_inscription": mortgage_inscription,
        "broker_buy": broker_buy,
        "renovation_cost": renovation_cost,
        "holding_costs": holding_costs,
        "holding_monthly": holding_monthly,
        "financing_costs": financing_costs,
        "total_investment": total_investment,
        # Verkoopzijde
        "arv": arv_mid,
        "arv_per_m2": arv_data["arv_per_m2"]["mid"],
        "broker_sell": broker_sell,
        "notary_sell": notary_sell,
        "net_sale_price": net_sale_price,
        # Resultaat
        "gross_profit": gross_profit,
        "roi": round(roi, 1),
        # Schattingen
        "renovation_estimate": reno,
        "arv_estimate": arv_data,
        "project_duration_months": project_months,
        "break_even_arv": break_even_arv,
        # Params
        "region": region,
        "ltv": ltv,
        "interest_rate": interest_rate,
    }


def calculate_sensitivity_be(listing: dict, params: dict,
                              overrides: dict | None = None) -> list[dict]:
    """
    Gevoeligheidsanalyse met 4 scenario's + break-even.
    """
    base = calculate_investment_analysis_be(listing, params, overrides)
    base_roi = base["roi"]
    base_profit = base["gross_profit"]

    scenarios = []

    # Scenario 1: Aankoopprijs 10% lager
    listing_s1 = {**listing, "price": round(listing["price"] * 0.90)}
    s1 = calculate_investment_analysis_be(listing_s1, params, overrides)
    scenarios.append({
        "scenario": "Aankoopprijs -10%",
        "roi": s1["roi"],
        "profit": s1["gross_profit"],
        "delta_roi": round(s1["roi"] - base_roi, 1),
        "delta_profit": s1["gross_profit"] - base_profit,
    })

    # Scenario 2: Renovatie 20% duurder
    reno_override = overrides.copy() if overrides else {}
    reno_m2 = base["renovation_estimate"]["adjusted_cost_m2"]
    reno_override["renovation_cost_m2"] = round(reno_m2 * 1.20)
    s2 = calculate_investment_analysis_be(listing, params, reno_override)
    scenarios.append({
        "scenario": "Renovatie +20%",
        "roi": s2["roi"],
        "profit": s2["gross_profit"],
        "delta_roi": round(s2["roi"] - base_roi, 1),
        "delta_profit": s2["gross_profit"] - base_profit,
    })

    # Scenario 3: Verkoopprijs 10% lager
    arv_override = overrides.copy() if overrides else {}
    arv_m2 = base["arv_per_m2"]
    arv_override["arv_m2"] = round(arv_m2 * 0.90)
    s3 = calculate_investment_analysis_be(listing, params, arv_override)
    scenarios.append({
        "scenario": "Verkoopprijs -10%",
        "roi": s3["roi"],
        "profit": s3["gross_profit"],
        "delta_roi": round(s3["roi"] - base_roi, 1),
        "delta_profit": s3["gross_profit"] - base_profit,
    })

    # Scenario 4: Projectduur +4 maanden
    params_s4 = {**params}
    extra_months = 4
    extra_holding = base["holding_monthly"] * extra_months
    extra_financing = round((base["purchase_price"] * base["ltv"] * base["interest_rate"] * extra_months) / 12)
    s4_profit = base_profit - extra_holding - extra_financing
    s4_invest = base["total_investment"] + extra_holding + extra_financing
    s4_roi = round((s4_profit / s4_invest * 100) if s4_invest > 0 else 0, 1)
    scenarios.append({
        "scenario": "Projectduur +4 maanden",
        "roi": s4_roi,
        "profit": s4_profit,
        "delta_roi": round(s4_roi - base_roi, 1),
        "delta_profit": s4_profit - base_profit,
    })

    return scenarios


def _excluded_result(listing: dict, reno: dict) -> dict:
    """Retourneert een lege analyse voor uitgesloten panden."""
    return {
        "purchase_price": listing.get("price", 0),
        "original_price": listing.get("price", 0),
        "total_investment": 0,
        "arv": 0,
        "gross_profit": 0,
        "roi": 0,
        "renovation_estimate": reno,
        "arv_estimate": {},
        "project_duration_months": 0,
        "is_excluded": True,
        "exclusion_reason": reno.get("exclusion_reason", "Buiten scope"),
    }
