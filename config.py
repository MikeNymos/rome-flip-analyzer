"""
Configureerbare parameters en defaults voor Rome Flip Analyzer.
"""
from __future__ import annotations


# === DESIGN SYSTEM ===
DESIGN = {
    # Light mode — soft warm cream
    "bg": "#FAF8F5",
    "bg_alt": "#F3F0EC",
    "card_bg": "#FFFFFF",
    "text_primary": "#1A1A2E",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "accent": "#E8956A",           # Warm coral — primary accent
    "accent_light": "#FBE8DE",
    "accent_dark": "#D4764A",
    "border": "rgba(0,0,0,0.06)",
    "shadow": "0 2px 16px rgba(0,0,0,0.05)",
    "card_radius": "20px",
    # Sidebar — modern dark slate (NOT brown)
    "sidebar_top": "#1E1E2E",
    "sidebar_bottom": "#151521",
    "sidebar_text": "#E2E8F0",
    "sidebar_muted": "#64748B",
    # Dark mode
    "dark_bg": "#0F0F1A",
    "dark_card": "#1A1A2E",
    "dark_border": "rgba(255,255,255,0.08)",
    "dark_text": "#E2E8F0",
    "dark_text_secondary": "#94A3B8",
    "dark_text_muted": "#475569",
    "dark_sidebar_top": "#0A0A18",
    "dark_sidebar_bottom": "#060612",
    # Score gradient colors
    "score_excellent": "#10B981",   # Emerald green
    "score_good": "#34D399",        # Lighter green
    "score_fair": "#F59E0B",        # Amber
    "score_poor": "#F97316",        # Orange
    "score_bad": "#EF4444",         # Red
    # Functional
    "positive": "#10B981",
    "negative": "#EF4444",
    "warning": "#F59E0B",
    # Multi-color accents (like reference images)
    "coral": "#E8956A",
    "emerald": "#10B981",
    "amber": "#F59E0B",
    "rose": "#F472B6",
    "indigo": "#818CF8",
    "sky": "#38BDF8",
    # Plotly
    "plotly_colorway": [
        "#E8956A", "#10B981", "#818CF8", "#F59E0B",
        "#F472B6", "#38BDF8", "#EF4444", "#94A3B8",
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
    (80, 101): ("Uitstekend", "#10B981", "Topkandidaat, direct actie ondernemen"),
    (65, 80): ("Goed", "#34D399", "Interessant, nader onderzoek waard"),
    (50, 65): ("Redelijk", "#F59E0B", "Potentieel, maar let op risico's"),
    (35, 50): ("Matig", "#F97316", "Waarschijnlijk niet winstgevend genoeg"),
    (0, 35): ("Slecht", "#EF4444", "Afwijzen"),
}

def get_score_label(score: int) -> tuple[str, str, str]:
    """Retourneert (label, kleur, betekenis) voor een flip score."""
    for (low, high), (label, color, meaning) in SCORE_LABELS.items():
        if low <= score < high:
            return label, color, meaning
    return "★ Slecht", "#c0392b", "Afwijzen"
