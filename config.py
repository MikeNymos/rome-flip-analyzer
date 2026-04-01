"""
Configureerbare parameters en defaults voor Rome Flip Analyzer.
"""
from __future__ import annotations


DEFAULT_PARAMS = {
    # Renovatie
    "renovation_cost_per_m2": 1500,
    "renovation_cost_min_per_m2": 1200,
    "renovation_cost_max_per_m2": 1800,

    # Bijkomende aankoopkosten
    "registration_tax_seconda_casa": 0.09,
    "registration_tax_prima_casa": 0.02,
    "notary_cost_fixed": 8000,
    "notary_cost_percentage": 0.015,
    "broker_buy_percentage": 0.03,
    "broker_sell_percentage": 0.03,

    # Architect & vergunningen
    "architect_geometra_cost": 25000,
    "architect_cost_percentage": 0.04,

    # Onvoorzien & holding
    "contingency_percentage": 0.12,
    "holding_cost_monthly": 1000,
    "project_duration_months": 14,

    # Fiscaal
    "plusvalenza_rate": 0.26,
    "plusvalenza_exempt_prima_casa": True,

    # Verkoopschattingen
    "asking_price_discount": 0.08,
    "renovated_premium_factor": 1.0,

    # Filters
    "min_roi_threshold": 15.0,
    "min_surface_m2": 80,
    "max_surface_m2": 200,
    "min_price": 200000,
    "max_price": 800000,
}

# Parameter beschrijvingen (Nederlands)
PARAM_DESCRIPTIONS = {
    "renovation_cost_per_m2": ("Renovatiekosten per m²", "Gemiddelde kosten voor high-end renovatie per vierkante meter"),
    "renovation_cost_min_per_m2": ("Renovatiekosten min per m²", "Ondergrens renovatiekosten (prima casa scenario)"),
    "renovation_cost_max_per_m2": ("Renovatiekosten max per m²", "Bovengrens renovatiekosten (seconda casa scenario)"),
    "registration_tax_seconda_casa": ("Registratiebelasting seconda casa", "9% registratiebelasting voor tweede woning"),
    "registration_tax_prima_casa": ("Registratiebelasting prima casa", "2% registratiebelasting voor eerste woning"),
    "notary_cost_fixed": ("Notariskosten (vast)", "Vast bedrag voor notaris en kadaster"),
    "notary_cost_percentage": ("Notariskosten (%)", "Percentage van aankoopprijs (hoogste van vast/percentage wordt genomen)"),
    "broker_buy_percentage": ("Makelaarscommissie aankoop", "Percentage makelaarskosten bij aankoop"),
    "broker_sell_percentage": ("Makelaarscommissie verkoop", "Percentage makelaarskosten bij verkoop"),
    "architect_geometra_cost": ("Architect + geometra (vast)", "Vast bedrag voor architect, geometra en vergunningen"),
    "architect_cost_percentage": ("Architect kosten (%)", "Percentage van renovatiekosten (hoogste van vast/percentage wordt genomen)"),
    "contingency_percentage": ("Onvoorziene kosten (%)", "Percentage extra op renovatiekosten voor onvoorziene uitgaven"),
    "holding_cost_monthly": ("Maandelijkse holding costs", "Maandelijkse kosten tijdens projectduur (lening, utilities, etc.)"),
    "project_duration_months": ("Projectduur (maanden)", "Verwachte totale projectduur van aankoop tot verkoop"),
    "plusvalenza_rate": ("Meerwaardebelasting (%)", "26% belasting op meerwaarde bij verkoop (seconda casa)"),
    "plusvalenza_exempt_prima_casa": ("Prima casa vrijstelling", "Geen meerwaardebelasting bij prima casa"),
    "asking_price_discount": ("Onderhandelingskorting", "Verwachte korting op vraagprijs bij aankoop"),
    "renovated_premium_factor": ("Gerenoveerde premie factor", "Multiplier op benchmark verkoopprijs"),
    "min_roi_threshold": ("Minimum ROI drempel (%)", "Minimale ROI om als interessant te worden beschouwd"),
    "min_surface_m2": ("Minimum oppervlakte (m²)", "Minimum oppervlakte filter"),
    "max_surface_m2": ("Maximum oppervlakte (m²)", "Maximum oppervlakte filter"),
    "min_price": ("Minimum prijs (€)", "Minimum aankoopprijs filter"),
    "max_price": ("Maximum prijs (€)", "Maximum aankoopprijs filter"),
}

# Score interpretatie
SCORE_LABELS = {
    (80, 101): ("★★★★★ Uitstekend", "#2d8a4e", "Topkandidaat, direct actie ondernemen"),
    (65, 80): ("★★★★ Goed", "#3da55d", "Interessant, nader onderzoek waard"),
    (50, 65): ("★★★ Redelijk", "#d4a017", "Potentieel, maar let op risico's"),
    (35, 50): ("★★ Matig", "#e07c24", "Waarschijnlijk niet winstgevend genoeg"),
    (0, 35): ("★ Slecht", "#c0392b", "Afwijzen"),
}

def get_score_label(score: int) -> tuple[str, str, str]:
    """Retourneert (label, kleur, betekenis) voor een flip score."""
    for (low, high), (label, color, meaning) in SCORE_LABELS.items():
        if low <= score < high:
            return label, color, meaning
    return "★ Slecht", "#c0392b", "Afwijzen"
