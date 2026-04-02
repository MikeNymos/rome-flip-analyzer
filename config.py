"""
Configureerbare parameters en defaults voor Rome Flip Analyzer.
"""
from __future__ import annotations


# === DESIGN SYSTEM ===
DESIGN = {
    # Light mode
    "bg": "#F5F0EB",
    "bg_alt": "#EDE7E0",
    "card_bg": "#FFFFFF",
    "text_primary": "#1A1A1A",
    "text_secondary": "#7A7672",
    "text_muted": "#B0AAA3",
    "accent": "#C9A24E",
    "accent_light": "#E8D5A0",
    "accent_dark": "#B8913D",
    "border": "rgba(0,0,0,0.06)",
    "shadow": "0 2px 12px rgba(0,0,0,0.04)",
    "card_radius": "20px",
    # Sidebar
    "sidebar_top": "#2C2520",
    "sidebar_bottom": "#1E1A17",
    "sidebar_text": "#E8E0D8",
    "sidebar_muted": "#8A8078",
    # Dark mode
    "dark_bg": "#1A1714",
    "dark_card": "#242018",
    "dark_border": "rgba(255,255,255,0.08)",
    "dark_text": "#E8E0D8",
    "dark_text_secondary": "#A09890",
    "dark_text_muted": "#6A6258",
    "dark_sidebar_top": "#141210",
    "dark_sidebar_bottom": "#0E0C0A",
    # Score colors
    "score_excellent": "#5B8A72",
    "score_good": "#7D9B8A",
    "score_fair": "#C9A24E",
    "score_poor": "#D4916A",
    "score_bad": "#D4766C",
    # Functional
    "positive": "#5B8A72",
    "negative": "#D4766C",
    "warning": "#D4916A",
    # Plotly
    "plotly_colorway": [
        "#C9A24E", "#7D9B8A", "#E8956A", "#4A6FA5",
        "#C4A0B9", "#D4766C", "#8B7E6A", "#B0AAA3",
    ],
}

DEFAULT_PARAMS = {
    # Renovatie
    "renovation_cost_per_m2": 2000,
    "renovation_cost_min_per_m2": 2000,
    "renovation_cost_max_per_m2": 2200,

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
    "asking_price_discount": 0.03,
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
    (80, 101): ("Uitstekend", "#5B8A72", "Topkandidaat, direct actie ondernemen"),
    (65, 80): ("Goed", "#7D9B8A", "Interessant, nader onderzoek waard"),
    (50, 65): ("Redelijk", "#C9A24E", "Potentieel, maar let op risico's"),
    (35, 50): ("Matig", "#D4916A", "Waarschijnlijk niet winstgevend genoeg"),
    (0, 35): ("Slecht", "#D4766C", "Afwijzen"),
}

def get_score_label(score: int) -> tuple[str, str, str]:
    """Retourneert (label, kleur, betekenis) voor een flip score."""
    for (low, high), (label, color, meaning) in SCORE_LABELS.items():
        if low <= score < high:
            return label, color, meaning
    return "★ Slecht", "#c0392b", "Afwijzen"
