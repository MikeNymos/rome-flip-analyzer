"""
Hulpfuncties voor formattering en data-verwerking.
"""
from __future__ import annotations


import locale


def format_eur(amount: float) -> str:
    """Formatteert een bedrag in Europees formaat: €1.234.567,89"""
    if amount >= 0:
        return f"€{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"-€{abs(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_eur_short(amount: float) -> str:
    """Kort formaat: €550K of €1,2M"""
    if abs(amount) >= 1_000_000:
        return f"€{amount / 1_000_000:,.1f}M".replace(".", ",")
    elif abs(amount) >= 1_000:
        return f"€{amount / 1_000:,.0f}K".replace(".", ",")
    else:
        return format_eur(amount)


def format_pct(value: float) -> str:
    """Formatteert een percentage: 12,4%"""
    return f"{value:,.1f}%".replace(".", ",")


def format_m2(value: float) -> str:
    """Formatteert vierkante meters."""
    return f"{value:,.0f} m²".replace(",", ".")


def format_eur_per_m2(amount: float) -> str:
    """Formatteert prijs per m²."""
    return f"€{amount:,.0f}/m²".replace(",", ".")


def safe_float(value, default: float = 0.0) -> float:
    """Veilig converteren naar float."""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            value = value.replace(".", "").replace(",", ".").replace("€", "").replace(" ", "")
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=None):
    """Veilig converteren naar int."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def score_color(score: int) -> str:
    """Retourneert een kleur op basis van de flip score (warm palette)."""
    if score >= 80:
        return "#5B8A72"
    elif score >= 65:
        return "#7D9B8A"
    elif score >= 50:
        return "#C9A24E"
    elif score >= 35:
        return "#D4916A"
    else:
        return "#D4766C"


def score_emoji(score: int) -> str:
    """Retourneert een label op basis van de flip score."""
    if score >= 80:
        return "Uitstekend"
    elif score >= 65:
        return "Goed"
    elif score >= 50:
        return "Redelijk"
    elif score >= 35:
        return "Matig"
    else:
        return "Slecht"


def get_plotly_layout(dark_mode: bool = False) -> dict:
    """Returns base Plotly layout kwargs matching the warm premium theme."""
    from config import DESIGN
    base = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, -apple-system, sans-serif", "size": 12},
        "colorway": DESIGN["plotly_colorway"],
    }
    if dark_mode:
        base["font"]["color"] = DESIGN["dark_text_secondary"]
    else:
        base["font"]["color"] = DESIGN["text_secondary"]
    return base
